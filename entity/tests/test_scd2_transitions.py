import pytest
from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from datetime import datetime, timedelta
from freezegun import freeze_time

from entity.models import Entity, EntityDetail
from entity.services.update import UpdateService
from entity.tests.factories import EntityFactory, EntityDetailFactory, EntityTypeFactory, DetailTypeFactory


@pytest.mark.django_db
@pytest.mark.scd2
class TestSCD2Transitions(TestCase):
    """Test SCD2 versioning behavior for entities and details."""
    
    def setUp(self):
        self.entity_type = EntityTypeFactory(code="PERSON", name="Person")
        self.detail_type = DetailTypeFactory(code="email", name="Email")
    
    def test_entity_update_creates_new_version(self):
        """Test that updating an entity creates a new version and closes the old one."""
        # Create initial entity
        entity = EntityFactory(
            display_name="John Doe",
            entity_type=self.entity_type
        )
        original_uid = entity.entity_uid
        
        # Update entity
        with freeze_time("2024-01-15 10:00:00"):
            payload = {
                "display_name": "John Smith",
                "entity_type": self.entity_type
            }
            new_entity = UpdateService.update_entity(str(original_uid), payload)
        
        # Verify two versions exist
        all_versions = Entity.objects.filter(entity_uid=original_uid).order_by('valid_from')
        self.assertEqual(all_versions.count(), 2)
        
        # Verify old version is closed
        old_version = all_versions.first()
        self.assertFalse(old_version.is_current)
        self.assertIsNotNone(old_version.valid_to)
        self.assertEqual(old_version.display_name, "John Doe")
        
        # Verify new version is current
        new_version = all_versions.last()
        self.assertTrue(new_version.is_current)
        self.assertIsNone(new_version.valid_to)
        self.assertEqual(new_version.display_name, "John Smith")
        self.assertEqual(new_version.entity_uid, original_uid)
    
    def test_detail_update_creates_new_version(self):
        """Test that updating entity details creates new detail versions."""
        entity = EntityFactory(entity_type=self.entity_type)
        
        # Create initial detail
        detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.detail_type,
            detail_value="john@old.com"
        )
        
        # Update entity with new detail
        with freeze_time("2024-01-15 10:00:00"):
            payload = {
                "display_name": entity.display_name,
                "entity_type": entity.entity_type,
                "details": [{
                    "detail_type": self.detail_type,
                    "detail_value": "john@new.com"
                }]
            }
            UpdateService.update_entity(str(entity.entity_uid), payload)
        
        # Verify two detail versions exist
        all_detail_versions = EntityDetail.objects.filter(
            entity__entity_uid=entity.entity_uid,
            detail_type=self.detail_type
        ).order_by('valid_from')
        self.assertEqual(all_detail_versions.count(), 2)
        
        # Verify old detail is closed
        old_detail = all_detail_versions.first()
        self.assertFalse(old_detail.is_current)
        self.assertIsNotNone(old_detail.valid_to)
        self.assertEqual(old_detail.detail_value, "john@old.com")
        
        # Verify new detail is current
        new_detail = all_detail_versions.last()
        self.assertTrue(new_detail.is_current)
        self.assertIsNone(new_detail.valid_to)
        self.assertEqual(new_detail.detail_value, "john@new.com")
    
    def test_partial_update_only_creates_necessary_versions(self):
        """Test that only changed fields create new versions."""
        entity = EntityFactory(entity_type=self.entity_type)
        email_detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.detail_type,
            detail_value="john@example.com"
        )
        
        phone_type = DetailTypeFactory(code="phone", name="Phone")
        phone_detail = EntityDetailFactory(
            entity=entity,
            detail_type=phone_type,
            detail_value="555-0123"
        )
        
        # Update only email, not phone
        payload = {
            "display_name": entity.display_name,  # Same value
            "entity_type": entity.entity_type,    # Same value
            "details": [{
                "detail_type": self.detail_type,
                "detail_value": "john@newcompany.com"  # Changed
            }, {
                "detail_type": phone_type,
                "detail_value": "555-0123"  # Same value
            }]
        }
        
        UpdateService.update_entity(str(entity.entity_uid), payload)
        
        # Email should have 2 versions (old + new)
        email_versions = EntityDetail.objects.filter(
            entity__entity_uid=entity.entity_uid,
            detail_type=self.detail_type
        )
        self.assertEqual(email_versions.count(), 2)
        
        # Phone should still have 1 version (unchanged)
        phone_versions = EntityDetail.objects.filter(
            entity__entity_uid=entity.entity_uid,
            detail_type=phone_type
        )
        self.assertEqual(phone_versions.count(), 1)
        self.assertTrue(phone_versions.first().is_current)
    
    def test_temporal_validity_windows_dont_overlap(self):
        """Test that validity windows don't overlap for the same entity."""
        entity = EntityFactory(entity_type=self.entity_type)
        
        # Update entity multiple times
        with freeze_time("2024-01-10 10:00:00"):
            UpdateService.update_entity(str(entity.entity_uid), {
                "display_name": "Version 2",
                "entity_type": entity.entity_type
            })
        
        with freeze_time("2024-01-15 10:00:00"):
            UpdateService.update_entity(str(entity.entity_uid), {
                "display_name": "Version 3", 
                "entity_type": entity.entity_type
            })
        
        # Get all versions ordered by time
        versions = Entity.objects.filter(
            entity_uid=entity.entity_uid
        ).order_by('valid_from')
        
        # Check that validity windows don't overlap
        for i in range(len(versions) - 1):
            current = versions[i]
            next_version = versions[i + 1]
            
            # Current version's valid_to should equal next version's valid_from
            self.assertEqual(current.valid_to, next_version.valid_from)
            
            # No gaps or overlaps
            self.assertLess(current.valid_from, current.valid_to)
            self.assertLess(current.valid_to, next_version.valid_from)
    
    def test_as_of_query_returns_correct_version(self):
        """Test that as-of queries return the correct historical version."""
        entity = EntityFactory(
            display_name="Original Name",
            entity_type=self.entity_type
        )
        
        # Update at specific times
        with freeze_time("2024-01-10 10:00:00"):
            UpdateService.update_entity(str(entity.entity_uid), {
                "display_name": "Updated Name",
                "entity_type": entity.entity_type
            })
        
        # Query as-of before update
        as_of_before = Entity.objects.filter(
            entity_uid=entity.entity_uid,
            valid_from__lte=datetime(2024, 1, 5, tzinfo=timezone.utc)
        ).filter(
            models.Q(valid_to__gt=datetime(2024, 1, 5, tzinfo=timezone.utc)) |
            models.Q(valid_to__isnull=True)
        ).first()
        
        self.assertIsNotNone(as_of_before)
        self.assertEqual(as_of_before.display_name, "Original Name")
        
        # Query as-of after update
        as_of_after = Entity.objects.filter(
            entity_uid=entity.entity_uid,
            valid_from__lte=datetime(2024, 1, 15, tzinfo=timezone.utc)
        ).filter(
            models.Q(valid_to__gt=datetime(2024, 1, 15, tzinfo=timezone.utc)) |
            models.Q(valid_to__isnull=True)
        ).first()
        
        self.assertIsNotNone(as_of_after)
        self.assertEqual(as_of_after.display_name, "Updated Name")
