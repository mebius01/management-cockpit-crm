import pytest
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta
from freezegun import freeze_time

from entity.models import Entity, EntityDetail
from entity.tests.factories import EntityFactory, EntityDetailFactory, EntityTypeFactory, DetailTypeFactory


@pytest.mark.django_db
@pytest.mark.api
class TestEntityAPIEndpoints(TestCase):
    """Test all Entity API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.entity_type = EntityTypeFactory(code="PERSON", name="Person")
        self.email_type = DetailTypeFactory(code="email", name="Email")
        self.phone_type = DetailTypeFactory(code="phone", name="Phone")
    
    def test_list_entities_endpoint(self):
        """Test GET /api/v1/entities endpoint."""
        # Create test entities
        entity1 = EntityFactory(
            display_name="John Doe",
            entity_type=self.entity_type
        )
        entity2 = EntityFactory(
            display_name="Jane Smith", 
            entity_type=self.entity_type
        )
        
        url = reverse('api:entities-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_list_entities_with_search(self):
        """Test GET /api/v1/entities with search parameter."""
        EntityFactory(display_name="John Doe", entity_type=self.entity_type)
        EntityFactory(display_name="Jane Smith", entity_type=self.entity_type)
        
        url = reverse('api:entities-list-create')
        response = self.client.get(url, {'q': 'john'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('John', response.data['results'][0]['display_name'])
    
    def test_list_entities_with_type_filter(self):
        """Test GET /api/v1/entities with entity_type filter."""
        person_type = EntityTypeFactory(code="PERSON", name="Person")
        company_type = EntityTypeFactory(code="COMPANY", name="Company")
        
        EntityFactory(display_name="John Doe", entity_type=person_type)
        EntityFactory(display_name="ACME Corp", entity_type=company_type)
        
        url = reverse('api:entities-list-create')
        response = self.client.get(url, {'entity_type': 'PERSON'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['entity_type'], 'PERSON')
    
    def test_create_entity_endpoint(self):
        """Test POST /api/v1/entities endpoint."""
        url = reverse('api:entities-list-create')
        payload = {
            "display_name": "New Person",
            "entity_type": "PERSON",
            "details": [
                {
                    "detail_type": "email",
                    "detail_value": "new@example.com"
                },
                {
                    "detail_type": "phone", 
                    "detail_value": "555-0123"
                }
            ]
        }
        
        response = self.client.post(
            url, 
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('entity', response.data)
        self.assertIn('details', response.data)
        self.assertEqual(response.data['entity']['display_name'], "New Person")
        self.assertEqual(len(response.data['details']), 2)
    
    def test_get_entity_snapshot_endpoint(self):
        """Test GET /api/v1/entities/{entity_uid} endpoint."""
        entity = EntityFactory(entity_type=self.entity_type)
        detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.email_type,
            detail_value="test@example.com"
        )
        
        url = reverse('api:entity-snapshot', kwargs={'entity_uid': entity.entity_uid})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('entity', response.data)
        self.assertIn('details', response.data)
        self.assertEqual(response.data['entity']['entity_uid'], str(entity.entity_uid))
        self.assertEqual(len(response.data['details']), 1)
    
    def test_update_entity_endpoint(self):
        """Test PATCH /api/v1/entities/{entity_uid} endpoint."""
        entity = EntityFactory(
            display_name="Original Name",
            entity_type=self.entity_type
        )
        
        url = reverse('api:entity-snapshot', kwargs={'entity_uid': entity.entity_uid})
        payload = {
            "display_name": "Updated Name",
            "details": [
                {
                    "detail_type": "email",
                    "detail_value": "updated@example.com"
                }
            ]
        }
        
        response = self.client.patch(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['entity']['display_name'], "Updated Name")
        
        # Verify SCD2 behavior - old version should exist
        all_versions = Entity.objects.filter(entity_uid=entity.entity_uid)
        self.assertEqual(all_versions.count(), 2)
    
    def test_entity_history_endpoint(self):
        """Test GET /api/v1/entities/{entity_uid}/history endpoint."""
        entity = EntityFactory(entity_type=self.entity_type)
        
        from entity.services.update import UpdateService

        # Create some history by updating
        with freeze_time("2024-01-10") as frozen_time:
            payload = {"display_name": "Version 2", "entity_type": self.entity_type.code}
            UpdateService.update_entity(str(entity.entity_uid), payload)
            
            frozen_time.tick(delta=timedelta(seconds=1))

            payload = {"display_name": "Version 3", "entity_type": self.entity_type.code}
            UpdateService.update_entity(str(entity.entity_uid), payload)
        
        url = reverse('api:entity-history', kwargs={'entity_uid': entity.entity_uid})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 3)  # Original + 2 updates
    
    def test_as_of_query_endpoint(self):
        """Test GET /api/v1/entities-asof endpoint."""
        with freeze_time("2024-01-01"):
            entity = EntityFactory(
                display_name="Original Name",
                entity_type=self.entity_type
            )
        
        with freeze_time("2024-01-10"):
            from entity.services.update import UpdateService
            UpdateService.update_entity(str(entity.entity_uid), {
                "display_name": "Updated Name",
                "entity_type": self.entity_type
            })
        
        # Query as-of before update
        url = reverse('api:entities-as-of')
        response = self.client.get(url, {'as_of': '2024-01-05'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['entity']['display_name'], "Original Name")
        
        # Query as-of after update
        response = self.client.get(url, {'as_of': '2024-01-15'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['entity']['display_name'], "Updated Name")
    
    def test_diff_endpoint(self):
        """Test GET /api/v1/diff endpoint."""
        with freeze_time("2024-01-01"):
            entity = EntityFactory(
                display_name="Original Name",
                entity_type=self.entity_type
            )
        
        with freeze_time("2024-01-10"):
            from entity.services.update import UpdateService
            UpdateService.update_entity(str(entity.entity_uid), {
                "display_name": "Updated Name",
                "entity_type": self.entity_type
            })
        
        url = reverse('api:entities-diff')
        response = self.client.get(url, {
            'from': '2024-01-01',
            'to': '2024-01-15'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        
        # Verify diff structure
        diff_entry = response.data[0]
        self.assertIn('entity_uid', diff_entry)
        self.assertIn('changes', diff_entry)
        self.assertTrue(len(diff_entry['changes']) > 0)
    
    def test_invalid_entity_uid_returns_404(self):
        """Test that invalid entity_uid returns 404."""
        import uuid
        invalid_uid = uuid.uuid4()
        
        url = reverse('api:entity-snapshot', kwargs={'entity_uid': invalid_uid})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_invalid_as_of_parameter_returns_400(self):
        """Test that invalid as_of parameter returns 400."""
        url = reverse('api:entities-as-of')
        response = self.client.get(url, {'as_of': 'invalid-date'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_missing_diff_parameters_returns_400(self):
        """Test that missing diff parameters return 400."""
        url = reverse('api:entities-diff')
        
        # Missing 'to' parameter
        response = self.client.get(url, {'from': '2024-01-01'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing 'from' parameter  
        response = self.client.get(url, {'to': '2024-01-15'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_entity_with_invalid_data_returns_400(self):
        """Test that creating entity with invalid data returns 400."""
        url = reverse('api:entities-list-create')
        
        # Missing required fields
        payload = {
            "display_name": "Test"
            # Missing entity_type
        }
        
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
