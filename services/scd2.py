from typing import Any, TypeVar

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# TypeVar for generic model (any model that inherits from models.Model)
ModelType = TypeVar("ModelType", bound=models.Model)


class SCD2Service:
    """Service for SCD Type 2 logic: creates new model version and closes old one."""

    # Common SCD2 fields that all models should have
    COMMON_REQUIRED_FIELDS = {"valid_from", "valid_to", "is_current", "updated_at"}
    
    # Model-specific required fields
    MODEL_SPECIFIC_FIELDS = {
        "Entity": {"entity_uid"},
        "EntityDetail": set(),  # EntityDetail doesn't have entity_uid
    }

    @classmethod
    def validate_fields(cls, instance: models.Model) -> None:
        """Validates presence of required fields in model instance."""
        model_name = instance.__class__.__name__
        required_fields = cls.COMMON_REQUIRED_FIELDS.copy()
        
        # Add model-specific fields if defined
        if model_name in cls.MODEL_SPECIFIC_FIELDS:
            required_fields.update(cls.MODEL_SPECIFIC_FIELDS[model_name])
        
        missing_fields = [
            field for field in required_fields if not hasattr(instance, field)
        ]
        if missing_fields:
            msg = f"Model {model_name} missing required SCD2 fields: {', '.join(missing_fields)}"
            raise ValidationError(msg)

    @classmethod
    def create_new_version(
        cls,
        old_instance: ModelType,
        **updates: Any,
    ) -> tuple[ModelType, ModelType]:
        """Creates new version, updates old one, returns both (without saving)."""
        cls.validate_fields(old_instance)

        now = timezone.now()
        new_instance = cls._copy_instance(old_instance)

        cls.setup_new_version(new_instance, now, updates)
        cls._close_old_version(old_instance, now)

        return old_instance, new_instance

    @classmethod
    def _copy_instance(cls, instance: ModelType) -> ModelType:
        """Copy all non-SCD2 fields from old instance to new one."""
        new_instance = type(instance)()

        # Copy all fields except SCD2 tracking fields
        exclude_fields = {
            "id",
            "pk",
            "valid_from",
            "valid_to",
            "is_current",
            "created_at",
            "updated_at",
        }

        for field in instance._meta.fields:
            if field.name not in exclude_fields:
                value = getattr(instance, field.name)
                setattr(new_instance, field.name, value)

        return new_instance

    @classmethod
    def setup_new_version(cls, instance: ModelType, now: Any, updates: dict) -> None:
        """Setup SCD2 fields and apply updates to new version."""
        instance.valid_from = now
        instance.valid_to = None
        instance.is_current = True
        instance.updated_at = now

        # Apply user updates
        for field, value in updates.items():
            setattr(instance, field, value)

    @classmethod
    def _close_old_version(cls, instance: ModelType, now: Any) -> None:
        """Close old version by setting SCD2 fields."""
        instance.valid_to = now
        instance.is_current = False
        instance.updated_at = now
