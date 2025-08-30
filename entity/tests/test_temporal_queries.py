import pytest
import uuid
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework import status

from entity.models import Entity, EntityDetail
from entity.tests.factories import EntityFactory, EntityDetailFactory, EntityTypeFactory, DetailTypeFactory
from entity.services import AsOfService, DiffService


@pytest.mark.django_db
@pytest.mark.temporal
class TestTemporalQueries(TestCase):
    """Test temporal query functionality for as-of and diff operations."""
    
    def setUp(self):
        self.client = APIClient()
        self.entity_type = EntityTypeFactory(code="PERSON", name="Person")
        self.email_type = DetailTypeFactory(code="email", name="Email")
        self.phone_type = DetailTypeFactory(code="phone", name="Phone")
        
        # Create test timeline
        self.base_time = timezone.now().replace(microsecond=0)
        self.t1 = self.base_time - timedelta(hours=3)
        self.t2 = self.base_time - timedelta(hours=2)
        self.t3 = self.base_time - timedelta(hours=1)
        self.t4 = self.base_time
    
    def create_entity_timeline(self):
        """Create an entity with multiple versions across time."""
        entity_uid = uuid.uuid4()
        
        # Version 1: t1 to t2
        with freeze_time(self.t1):
            entity_v1 = Entity.objects.create(
                entity_uid=entity_uid,
                display_name="John Doe v1",
                entity_type=self.entity_type,
                valid_from=self.t1,
                valid_to=self.t2,
                is_current=False
            )
            
            email_v1 = EntityDetail.objects.create(
                entity=entity_v1,
                detail_type=self.email_type,
                detail_value="john.v1@example.com",
                valid_from=self.t1,
                valid_to=self.t2,
                is_current=False
            )
        
        # Version 2: t2 to t3
        with freeze_time(self.t2):
            entity_v2 = Entity.objects.create(
                entity_uid=entity_uid,
                display_name="John Doe v2",
                entity_type=self.entity_type,
                valid_from=self.t2,
                valid_to=self.t3,
                is_current=False
            )
            
            email_v2 = EntityDetail.objects.create(
                entity=entity_v2,
                detail_type=self.email_type,
                detail_value="john.v2@example.com",
                valid_from=self.t2,
                valid_to=self.t3,
                is_current=False
            )
            
            # Add phone in v2
            phone_v2 = EntityDetail.objects.create(
                entity=entity_v2,
                detail_type=self.phone_type,
                detail_value="555-0001",
                valid_from=self.t2,
                valid_to=self.t3,
                is_current=False
            )
        
        # Version 3: t3 to infinity (current)
        with freeze_time(self.t3):
            entity_v3 = Entity.objects.create(
                entity_uid=entity_uid,
                display_name="John Doe v3",
                entity_type=self.entity_type,
                valid_from=self.t3,
                is_current=True
            )
            
            email_v3 = EntityDetail.objects.create(
                entity=entity_v3,
                detail_type=self.email_type,
                detail_value="john.v3@example.com",
                valid_from=self.t3,
                is_current=True
            )
            
            # Phone updated in v3
            phone_v3 = EntityDetail.objects.create(
                entity=entity_v3,
                detail_type=self.phone_type,
                detail_value="555-0002",
                valid_from=self.t3,
                is_current=True
            )
        
        return entity_uid


class TestAsOfService(TestTemporalQueries):
    """Test AsOfService functionality."""
    
    def test_asof_service_at_t1(self):
        """Test as-of query at t1 returns version 1."""
        entity_uid = self.create_entity_timeline()
        
        queryset = AsOfService.get_queryset({'asof': self.t1.isoformat()})
        entities = list(queryset)
        
        self.assertEqual(len(entities), 1)
        entity = entities[0]
        self.assertEqual(entity.entity_uid, entity_uid)
        self.assertEqual(entity.display_name, "John Doe v1")
        self.assertEqual(len(entity.details), 1)
        self.assertEqual(entity.details[0]['detail_value'], "john.v1@example.com")
        self.assertEqual(str(entity.entity_uid), str(entity_uid))
    
    def test_asof_service_at_t2(self):
        """Test as-of query at t2 returns version 2."""
        entity_uid = self.create_entity_timeline()
        
        queryset = AsOfService.get_queryset({'asof': self.t2.isoformat()})
        entities = list(queryset)
        
        self.assertEqual(len(entities), 1)
        entity = entities[0]
        self.assertEqual(entity.display_name, "John Doe v2")
        self.assertEqual(len(entity.details), 2)  # email + phone
        self.assertEqual(str(entity.entity_uid), str(entity_uid))
        
        detail_values = {d['detail_type__code']: d['detail_value'] for d in entity.details}
        self.assertEqual(detail_values['email'], "john.v2@example.com")
        self.assertEqual(detail_values['phone'], "555-0001")
    
    def test_asof_service_at_t3(self):
        """Test as-of query at t3 returns version 3."""
        entity_uid = self.create_entity_timeline()
        
        queryset = AsOfService.get_queryset({'asof': self.t3.isoformat()})
        entities = list(queryset)
        
        self.assertEqual(len(entities), 1)
        entity = entities[0]
        self.assertEqual(entity.display_name, "John Doe v3")
        self.assertEqual(len(entity.details), 2)
        self.assertEqual(str(entity.entity_uid), str(entity_uid))
        
        detail_values = {d['detail_type__code']: d['detail_value'] for d in entity.details}
        self.assertEqual(detail_values['email'], "john.v3@example.com")
        self.assertEqual(detail_values['phone'], "555-0002")
    
    def test_asof_service_before_entity_exists(self):
        """Test as-of query before entity exists returns empty."""
        self.create_entity_timeline()
        before_time = self.t1 - timedelta(hours=1)
        
        queryset = AsOfService.get_queryset({'asof': before_time.isoformat()})
        entities = list(queryset)
        
        self.assertEqual(len(entities), 0)
    
    def test_asof_service_with_filters(self):
        """Test as-of query with additional filters."""
        entity_uid = self.create_entity_timeline()
        
        # Create another entity
        other_entity = EntityFactory(
            display_name="Other Entity",
            entity_type=self.entity_type
        )
        
        # Query with entity_uid filter
        queryset = AsOfService.get_queryset({
            'asof': self.t2.isoformat(),
            'entity_uid': str(entity_uid)
        })
        entities = list(queryset)
        
        self.assertEqual(len(entities), 1)
        self.assertEqual(str(entities[0].entity_uid), str(entity_uid))


class TestDiffService(TestTemporalQueries):
    """Test DiffService functionality."""
    
    def test_diff_service_between_t1_and_t2(self):
        """Test diff between t1 and t2."""
        entity_uid = self.create_entity_timeline()
        
        diff_result = DiffService.get_entities_diff(self.t1, self.t2)
        
        self.assertEqual(len(diff_result), 1)
        diff_entity = diff_result[0]
        
        self.assertEqual(str(diff_entity['entity_uid']), str(entity_uid))
        self.assertEqual(diff_entity['from_snapshot']['display_name'], "John Doe v1")
        self.assertEqual(diff_entity['to_snapshot']['display_name'], "John Doe v2")
        
        # Check detail changes
        from_details = {d['detail_type__code']: d['detail_value'] 
                       for d in diff_entity['from_snapshot']['details']}
        to_details = {d['detail_type__code']: d['detail_value'] 
                     for d in diff_entity['to_snapshot']['details']}
        
        self.assertEqual(from_details['email'], "john.v1@example.com")
        self.assertEqual(to_details['email'], "john.v2@example.com")
        self.assertNotIn('phone', from_details)
        self.assertEqual(to_details['phone'], "555-0001")
    
    def test_diff_service_between_t2_and_t3(self):
        """Test diff between t2 and t3."""
        entity_uid = self.create_entity_timeline()
        
        diff_result = DiffService.get_entities_diff(self.t2, self.t3)
        
        self.assertEqual(len(diff_result), 1)
        diff_entity = diff_result[0]
        
        # Check phone number change
        from_details = {d['detail_type__code']: d['detail_value'] 
                       for d in diff_entity['from_snapshot']['details']}
        to_details = {d['detail_type__code']: d['detail_value'] 
                     for d in diff_entity['to_snapshot']['details']}
        
        self.assertEqual(from_details['phone'], "555-0001")
        self.assertEqual(to_details['phone'], "555-0002")
    
    def test_diff_service_no_changes(self):
        """Test diff when no changes occurred."""
        # Create entity that doesn't change
        entity = EntityFactory(entity_type=self.entity_type)
        
        # Query diff within same time period
        diff_result = DiffService.get_entities_diff(self.t3, self.t4)
        
        # Should return empty list (no entities changed)
        self.assertEqual(len(diff_result), 0)
    
    def test_diff_service_entity_created(self):
        """Test diff when entity is created between timepoints."""
        # Create entity at t2
        with freeze_time(self.t2):
            entity = EntityFactory(
                entity_type=self.entity_type,
                valid_from=self.t2
            )
        
        # Diff from t1 to t3 should show creation
        diff_result = DiffService.get_entities_diff(self.t1, self.t3)
        
        self.assertEqual(len(diff_result), 1)
        diff_entity = diff_result[0]
        
        self.assertEqual(str(diff_entity['entity_uid']), str(entity.entity_uid))
        self.assertIsNone(diff_entity['from_snapshot'])  # Didn't exist at t1
        self.assertIsNotNone(diff_entity['to_snapshot'])  # Exists at t3


class TestTemporalAPIEndpoints(TestTemporalQueries):
    """Test temporal query API endpoints."""
    
    def test_asof_api_endpoint(self):
        """Test GET /entities-asof API endpoint."""
        entity_uid = self.create_entity_timeline()
        
        url = reverse('api:entities-as-of')
        response = self.client.get(url, {
            'asof': self.t2.isoformat()
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['results']
        
        self.assertEqual(len(data), 1)
        entity = data[0]
        self.assertEqual(entity['entity_uid'], str(entity_uid))
        self.assertEqual(entity['display_name'], "John Doe v2")
        self.assertEqual(len(entity['details']), 2)
    
    def test_asof_api_invalid_datetime(self):
        """Test as-of API with invalid datetime format."""
        url = reverse('api:entities-as-of')
        response = self.client.get(url, {
            'asof': 'invalid-datetime'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('asof', response.json())
    
    def test_asof_api_missing_parameter(self):
        """Test as-of API without required asof parameter."""
        url = reverse('api:entities-as-of')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('asof', response.json())
    
    def test_diff_api_endpoint(self):
        """Test GET /diff API endpoint."""
        entity_uid = self.create_entity_timeline()
        
        url = reverse('api:entities-diff')
        response = self.client.get(url, {
            'fr': self.t1.isoformat(),
            'to': self.t2.isoformat()
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data), 1)
        diff_entity = data[0]
        self.assertEqual(diff_entity['entity_uid'], str(entity_uid))
        self.assertIsNotNone(diff_entity['from_snapshot'])
        self.assertIsNotNone(diff_entity['to_snapshot'])
    
    def test_diff_api_invalid_order(self):
        """Test diff API with fr > to (invalid order)."""
        url = reverse('api:entities-diff')
        response = self.client.get(url, {
            'fr': self.t2.isoformat(),
            'to': self.t1.isoformat()  # Earlier than fr
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fr', response.json())
    
    def test_diff_api_missing_parameters(self):
        """Test diff API without required parameters."""
        url = reverse('api:entities-diff')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fr', response.json())
        self.assertIn('to', response.json())
    
    def test_diff_api_partial_parameters(self):
        """Test diff API with only one parameter."""
        url = reverse('api:entities-diff')
        response = self.client.get(url, {'fr': self.t1.isoformat()})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('to', response.json())
    
    def test_temporal_queries_with_timezone_aware_datetimes(self):
        """Test temporal queries handle timezone-aware datetimes correctly."""
        entity_uid = self.create_entity_timeline()
        
        # Use ISO format with timezone
        asof_time = self.t2.isoformat()
        
        url = reverse('api:entities-as-of')
        response = self.client.get(url, {'asof': asof_time})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['results']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['entity_uid'], str(entity_uid))
    
    def test_temporal_edge_case_exact_boundary(self):
        """Test temporal queries at exact validity boundaries."""
        entity_uid = self.create_entity_timeline()
        
        # Query exactly at t2 (boundary between v1 and v2)
        url = reverse('api:entities-as-of')
        response = self.client.get(url, {
            'asof': self.t2.isoformat()
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['results']
        
        # Should return v2 (t2 is start of v2's validity)
        self.assertEqual(data[0]['display_name'], "John Doe v2")
    
    def test_multiple_entities_temporal_query(self):
        """Test temporal queries with multiple entities."""
        # Create first entity timeline
        entity_uid_1 = self.create_entity_timeline()
        
        # Create second entity
        with freeze_time(self.t2):
            entity_2 = EntityFactory(
                display_name="Jane Smith",
                entity_type=self.entity_type,
                valid_from=self.t2
            )
        
        # Query at t3 should return both entities
        url = reverse('api:entities-as-of')
        response = self.client.get(url, {
            'asof': self.t3.isoformat()
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['results']
        
        self.assertEqual(len(data), 2)
        entity_uids = {entity['entity_uid'] for entity in data}
        self.assertEqual(entity_uids, {str(entity_uid_1), str(entity_2.entity_uid)})
