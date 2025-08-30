import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from freezegun import freeze_time

from entity.models import Entity, EntityDetail
from entity.services.update import UpdateService
from entity.tests.factories import EntityFactory, EntityDetailFactory, EntityTypeFactory, DetailTypeFactory


@pytest.mark.django_db
@pytest.mark.idempotency
class TestIdempotencyBehavior(TestCase):
    """Test idempotent update operations."""
    
    def setUp(self):
        self.entity_type = EntityTypeFactory(code="PERSON", name="Person")
        self.email_type = DetailTypeFactory(code="email", name="Email")
        self.phone_type = DetailTypeFactory(code="phone", name="Phone")
    
    def test_identical_entity_update_is_noop(self):
        """Test that identical entity updates don't create new versions."""
        entity = EntityFactory(
            display_name="John Doe",
            entity_type=self.entity_type
        )
        
        # Update with identical data
        payload = {
            "display_name": "John Doe",  # Same value
            "entity_type": self.entity_type  # Same value
        }
        
        result_entity, was_changed = UpdateService.update_entity_idempotent(
            str(entity.entity_uid), payload
        )
        
        # Should return original entity unchanged
        self.assertFalse(was_changed)
        self.assertEqual(result_entity.id, entity.id)
        
        # Should still have only one version
        all_versions = Entity.objects.filter(entity_uid=entity.entity_uid)
        self.assertEqual(all_versions.count(), 1)
    
    def test_identical_detail_update_is_noop(self):
        """Test that identical detail updates don't create new versions."""
        entity = EntityFactory(entity_type=self.entity_type)
        detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.email_type,
            detail_value="john@example.com"
        )
        
        # Update with identical detail data
        payload = {
            "display_name": entity.display_name,
            "entity_type": entity.entity_type,
            "details": [{
                "detail_type": self.email_type,
                "detail_value": "john@example.com"  # Same value
            }]
        }
        
        result_entity, was_changed = UpdateService.update_entity_idempotent(
            str(entity.entity_uid), payload
        )
        
        # Should not create new versions
        self.assertFalse(was_changed)
        
        # Should still have only one entity version
        entity_versions = Entity.objects.filter(entity_uid=entity.entity_uid)
        self.assertEqual(entity_versions.count(), 1)
        
        # Should still have only one detail version
        detail_versions = EntityDetail.objects.filter(
            entity__entity_uid=entity.entity_uid,
            detail_type=self.email_type
        )
        self.assertEqual(detail_versions.count(), 1)
    
    def test_case_insensitive_idempotency(self):
        """Test that case differences don't create new versions."""
        entity = EntityFactory(
            display_name="John Doe",
            entity_type=self.entity_type
        )
        detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.email_type,
            detail_value="john@example.com"
        )
        
        # Update with case differences
        payload = {
            "display_name": "JOHN DOE",  # Different case
            "entity_type": entity.entity_type,
            "details": [{
                "detail_type": self.email_type,
                "detail_value": "JOHN@EXAMPLE.COM"  # Different case
            }]
        }
        
        result_entity, was_changed = UpdateService.update_entity_idempotent(
            str(entity.entity_uid), payload
        )
        
        # Should not create new versions (case-insensitive)
        self.assertFalse(was_changed)
        
        # Should still have only one version each
        entity_versions = Entity.objects.filter(entity_uid=entity.entity_uid)
        self.assertEqual(entity_versions.count(), 1)
        
        detail_versions = EntityDetail.objects.filter(
            entity__entity_uid=entity.entity_uid,
            detail_type=self.email_type
        )
        self.assertEqual(detail_versions.count(), 1)
    
    def test_whitespace_differences_are_ignored(self):
        """Test that whitespace differences don't create new versions."""
        entity = EntityFactory(
            display_name="John Doe",
            entity_type=self.entity_type
        )
        detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.email_type,
            detail_value="john@example.com"
        )
        
        # Update with whitespace differences
        payload = {
            "display_name": "  John Doe  ",  # Extra whitespace
            "entity_type": entity.entity_type,
            "details": [{
                "detail_type": self.email_type,
                "detail_value": "  john@example.com  "  # Extra whitespace
            }]
        }
        
        result_entity, was_changed = UpdateService.update_entity_idempotent(
            str(entity.entity_uid), payload
        )
        
        # Should not create new versions (whitespace-insensitive)
        self.assertFalse(was_changed)
        
        # Should still have only one version each
        entity_versions = Entity.objects.filter(entity_uid=entity.entity_uid)
        self.assertEqual(entity_versions.count(), 1)
        
        detail_versions = EntityDetail.objects.filter(
            entity__entity_uid=entity.entity_uid,
            detail_type=self.email_type
        )
        self.assertEqual(detail_versions.count(), 1)
    
    def test_replay_with_same_timestamp_is_idempotent(self):
        """Test that replaying updates with same timestamp is idempotent."""
        entity = EntityFactory(entity_type=self.entity_type)
        
        change_timestamp = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        
        payload = {
            "display_name": "Updated Name",
            "entity_type": entity.entity_type
        }
        
        # First update
        result1, changed1 = UpdateService.update_entity_idempotent(
            str(entity.entity_uid), payload, change_timestamp
        )
        self.assertTrue(changed1)
        
        # Replay same update with same timestamp
        result2, changed2 = UpdateService.update_entity_idempotent(
            str(entity.entity_uid), payload, change_timestamp
        )
        self.assertFalse(changed2)
        
        # Should have only 2 versions (original + first update)
        all_versions = Entity.objects.filter(entity_uid=entity.entity_uid)
        self.assertEqual(all_versions.count(), 2)
    
    def test_partial_changes_only_affect_changed_fields(self):
        """Test that only changed fields create new versions."""
        entity = EntityFactory(entity_type=self.entity_type)
        email_detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.email_type,
            detail_value="john@old.com"
        )
        phone_detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.phone_type,
            detail_value="555-0123"
        )
        
        # Update only email, keep phone same
        payload = {
            "display_name": entity.display_name,  # Same
            "entity_type": entity.entity_type,    # Same
            "details": [{
                "detail_type": self.email_type,
                "detail_value": "john@new.com"  # Changed
            }, {
                "detail_type": self.phone_type,
                "detail_value": "555-0123"  # Same
            }]
        }
        
        result_entity, was_changed = UpdateService.update_entity_idempotent(
            str(entity.entity_uid), payload
        )
        
        self.assertTrue(was_changed)
        
        # Entity should have 2 versions (original + update for consistency)
        entity_versions = Entity.objects.filter(entity_uid=entity.entity_uid)
        self.assertEqual(entity_versions.count(), 2)
        
        # Email should have 2 versions (old + new)
        email_versions = EntityDetail.objects.filter(
            entity__entity_uid=entity.entity_uid,
            detail_type=self.email_type
        )
        self.assertEqual(email_versions.count(), 2)
        
        # Phone should have 1 version (unchanged)
        phone_versions = EntityDetail.objects.filter(
            entity__entity_uid=entity.entity_uid,
            detail_type=self.phone_type
        )
        self.assertEqual(phone_versions.count(), 1)
        self.assertTrue(phone_versions.first().is_current)
    
    def test_hashdiff_computation_consistency(self):
        """Test that hashdiff computation is consistent."""
        entity = EntityFactory(entity_type=self.entity_type)
        
        # Create detail with specific value
        detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.email_type,
            detail_value="test@example.com"
        )
        
        original_hashdiff = detail.hashdiff
        
        # Save again - hashdiff should be same
        detail.save()
        self.assertEqual(detail.hashdiff, original_hashdiff)
        
        # Create another detail with same value
        entity2 = EntityFactory(entity_type=self.entity_type)
        detail2 = EntityDetailFactory(
            entity=entity2,
            detail_type=self.email_type,
            detail_value="test@example.com"
        )
        
        # Should have same hashdiff
        self.assertEqual(detail.hashdiff, detail2.hashdiff)
    
    def test_mixed_changes_and_no_changes(self):
        """Test updates with mix of changed and unchanged values."""
        entity = EntityFactory(
            display_name="Original Name",
            entity_type=self.entity_type
        )
        email_detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.email_type,
            detail_value="old@example.com"
        )
        phone_detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.phone_type,
            detail_value="555-0123"
        )
        
        # Change entity name and email, keep phone same
        payload = {
            "display_name": "New Name",  # Changed
            "entity_type": entity.entity_type,  # Same
            "details": [{
                "detail_type": self.email_type,
                "detail_value": "new@example.com"  # Changed
            }, {
                "detail_type": self.phone_type,
                "detail_value": "555-0123"  # Same
            }]
        }
        
        result_entity, was_changed = UpdateService.update_entity_idempotent(
            str(entity.entity_uid), payload
        )
        
        self.assertTrue(was_changed)
        
        # Verify final state
        current_entity = Entity.objects.get(
            entity_uid=entity.entity_uid,
            is_current=True
        )
        self.assertEqual(current_entity.display_name, "New Name")
        
        current_email = EntityDetail.objects.get(
            entity__entity_uid=entity.entity_uid,
            detail_type=self.email_type,
            is_current=True
        )
        self.assertEqual(current_email.detail_value, "new@example.com")
        
        current_phone = EntityDetail.objects.get(
            entity__entity_uid=entity.entity_uid,
            detail_type=self.phone_type,
            is_current=True
        )
        self.assertEqual(current_phone.detail_value, "555-0123")
