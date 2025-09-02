import pytest
from django.test import TestCase
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import datetime, timedelta
from freezegun import freeze_time

from entity.models import Entity, EntityDetail
from entity.tests.factories import EntityFactory, EntityDetailFactory, EntityTypeFactory, DetailTypeFactory


@pytest.mark.django_db
@pytest.mark.constraints
class TestDatabaseConstraints(TestCase):
    """Test database constraint violations."""
    
    def setUp(self):
        self.entity_type = EntityTypeFactory(code="PERSON", name="Person")
        self.email_type = DetailTypeFactory(code="email", name="Email")
    
    def test_unique_current_entity_constraint(self):
        """Test that only one current entity per entity_uid is allowed."""
        entity = EntityFactory(entity_type=self.entity_type)
        
        # Try to create another current entity with same entity_uid
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Entity.objects.create(
                    entity_uid=entity.entity_uid,
                    display_name="Duplicate Current",
                    entity_type=self.entity_type,
                    is_current=True
                )
    
    def test_unique_current_detail_constraint(self):
        """Test that only one current detail per entity+detail_type is allowed."""
        entity = EntityFactory(entity_type=self.entity_type)
        detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.email_type,
            is_current=True
        )
        
        # Try to create another current detail for same entity+type
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EntityDetail.objects.create(
                    entity=entity,
                    detail_type=self.email_type,
                    detail_value="duplicate@example.com",
                    is_current=True
                )
    
    def test_entity_exclusion_constraint_prevents_overlaps(self):
        """Test that overlapping validity periods are prevented for entities."""
        entity = EntityFactory(entity_type=self.entity_type)
        
        # Close the current entity
        entity.is_current = False
        entity.valid_to = timezone.now() + timedelta(hours=1)
        entity.save()
        
        # Try to create overlapping entity version
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Entity.objects.create(
                    entity_uid=entity.entity_uid,
                    display_name="Overlapping Version",
                    entity_type=self.entity_type,
                    valid_from=timezone.now() - timedelta(hours=1),  # Overlaps with existing
                    valid_to=timezone.now() + timedelta(hours=2),
                    is_current=False
                )
    
    def test_detail_exclusion_constraint_prevents_overlaps(self):
        """Test that overlapping validity periods are prevented for details."""
        entity = EntityFactory(entity_type=self.entity_type)
        detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.email_type
        )
        
        # Close the current detail
        detail.is_current = False
        detail.valid_to = timezone.now() + timedelta(hours=1)
        detail.save()
        
        # Try to create overlapping detail version
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EntityDetail.objects.create(
                    entity=entity,
                    detail_type=self.email_type,
                    detail_value="overlapping@example.com",
                    valid_from=timezone.now() - timedelta(hours=1),  # Overlaps
                    valid_to=timezone.now() + timedelta(hours=2),
                    is_current=False
                )
    
    def test_adjacent_validity_periods_are_allowed(self):
        """Test that adjacent (non-overlapping) validity periods are allowed."""
        entity = EntityFactory(entity_type=self.entity_type)
        
        # Close current entity at specific time
        cutoff_time = timezone.now() + timedelta(hours=1)
        entity.is_current = False
        entity.valid_to = cutoff_time
        entity.save()
        
        # Create new version starting exactly when old one ends
        new_entity = Entity.objects.create(
            entity_uid=entity.entity_uid,
            display_name="Adjacent Version",
            entity_type=self.entity_type,
            valid_from=cutoff_time,  # Starts exactly when previous ends
            is_current=True
        )
        
        # Should succeed without constraint violation
        self.assertIsNotNone(new_entity.id)
    
    def test_multiple_non_current_entities_allowed(self):
        """Test that multiple non-current entities with same entity_uid are allowed."""
        entity_uid = EntityFactory(entity_type=self.entity_type).entity_uid
        
        # Create multiple historical versions
        for i in range(3):
            Entity.objects.create(
                entity_uid=entity_uid,
                display_name=f"Historical Version {i}",
                entity_type=self.entity_type,
                valid_from=timezone.now() - timedelta(days=i+1),
                valid_to=timezone.now() - timedelta(days=i),
                is_current=False
            )
        
        # Should have 4 total entities (original + 3 historical)
        all_entities = Entity.objects.filter(entity_uid=entity_uid)
        self.assertEqual(all_entities.count(), 4)
    
    def test_entity_type_foreign_key_constraint(self):
        """Test that entity_type foreign key constraint is enforced."""
        # Try to create entity with non-existent entity_type_id
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Entity.objects.create(
                    display_name="Invalid Entity",
                    entity_type_id=99999,  # Non-existent ID
                    is_current=True
                )
    
    def test_detail_type_foreign_key_constraint(self):
        """Test that detail_type foreign key constraint is enforced."""
        entity = EntityFactory(entity_type=self.entity_type)
        
        # Try to create detail with non-existent detail_type_id
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EntityDetail.objects.create(
                    entity=entity,
                    detail_type_id=99999,  # Non-existent ID
                    detail_value="test value",
                    is_current=True
                )
    
    def test_entity_cascade_delete_constraint(self):
        """Test that deleting entity cascades to details."""
        entity = EntityFactory(entity_type=self.entity_type)
        detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.email_type
        )
        
        detail_id = detail.id
        
        # Delete entity
        entity.delete()
        
        # Detail should be deleted too
        with self.assertRaises(EntityDetail.DoesNotExist):
            EntityDetail.objects.get(id=detail_id)
    
    def test_entity_type_protect_constraint(self):
        """Test that entity_type cannot be deleted if entities reference it."""
        entity = EntityFactory(entity_type=self.entity_type)
        
        # Try to delete entity_type that's referenced
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.entity_type.delete()
    
    def test_detail_type_protect_constraint(self):
        """Test that detail_type cannot be deleted if details reference it."""
        entity = EntityFactory(entity_type=self.entity_type)
        detail = EntityDetailFactory(
            entity=entity,
            detail_type=self.email_type
        )
        
        # Try to delete detail_type that's referenced
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.email_type.delete()
    
    def test_valid_from_not_null_constraint(self):
        """Test that valid_from cannot be null."""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Entity.objects.create(
                    display_name="Invalid Entity",
                    entity_type=self.entity_type,
                    valid_from=None,  # Should not be allowed
                    is_current=True
                )
    
    def test_display_name_not_null_constraint(self):
        """Test that display_name cannot be null."""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Entity.objects.create(
                    display_name=None,  # Should not be allowed
                    entity_type=self.entity_type,
                    is_current=True
                )
    
    def test_detail_value_not_null_constraint(self):
        """Test that detail_value cannot be null."""
        entity = EntityFactory(entity_type=self.entity_type)
        
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                EntityDetail.objects.create(
                    entity=entity,
                    detail_type=self.email_type,
                    detail_value=None,  # Should not be allowed
                    is_current=True
                )
    
    def test_temporal_constraint_with_null_valid_to(self):
        """Test that null valid_to (infinity) works with exclusion constraints."""
        entity = EntityFactory(entity_type=self.entity_type)
        
        # Current entity has valid_to=null (infinity)
        self.assertIsNone(entity.valid_to)
        self.assertTrue(entity.is_current)
        
        # Try to create another entity with overlapping period
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Entity.objects.create(
                    entity_uid=entity.entity_uid,
                    display_name="Overlapping with Infinity",
                    entity_type=self.entity_type,
                    valid_from=timezone.now() + timedelta(hours=1),
                    valid_to=None,  # Also infinity - should conflict
                    is_current=False
                )
