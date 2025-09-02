from typing import Any, Dict, Optional
from datetime import datetime
import zoneinfo

from django.db import transaction
from django.utils import timezone
from django.db.models import Model
from services.datetime import DateTimeService


class SCD2Service:
    """
    Service for implementing Slowly Changing Dimension Type 2 (SCD2) mechanism.

    SCD2 allows storing complete historical sequence of changes for each entity
    by maintaining versioned records in the same table with temporal attributes.
    """

    SYSTEM_FIELDS = {"valid_from", "valid_to", "is_current", "created_at", "updated_at"}
    REQUIRED_SYSTEM_FIELDS = {
        "valid_from",
        "valid_to",
        "is_current",
        "created_at",
        "updated_at",
    }

    @classmethod
    def _validate_current_data(cls, data: Dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValueError("current_data must be a dict")

        missing = cls.REQUIRED_SYSTEM_FIELDS - data.keys()
        if missing:
            raise ValueError(f"current_data missing required fields: {sorted(missing)}")

        # Validate SCD2 state of the current record
        if data.get("is_current") is not True:
            raise ValueError(
                "current_data must represent the current record: is_current must be True"
            )

        if data.get("valid_to") is not None:
            raise ValueError(
                "current_data must have valid_to=None for an open/current version"
            )

        # Validate datetime formats (accept datetime or ISO strings)
        for key in ("valid_from", "created_at", "updated_at"):
            try:
                DateTimeService.validate_and_parse(data.get(key))
            except Exception as e:
                raise ValueError(f"Invalid datetime for '{key}': {e}")

    @classmethod
    @transaction.atomic
    def build_version_transition(
        cls,
        current_data: Dict[str, Any],
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Build SCD2 payloads for closing the current version and opening a new one.

        Args:
            current_data: Dict of the current record's fields including SCD2 system fields.
            now: Optional explicit timestamp; if not provided, uses timezone.now() in UTC.

        Returns:
            {
                "old_data": { ...current_data..., valid_to=now, is_current=False, updated_at=now },
                "new_data": { ...non-system fields..., valid_from=now, valid_to=None,
                               is_current=True, created_at=now, updated_at=now }
            }
        """
        if current_data is None:
            raise ValueError("current_data must be provided")

        # Validate incoming current record payload
        cls._validate_current_data(current_data)

        # Use UTC datetime
        now_dt = now or timezone.now()
        now_dt = now_dt.astimezone(zoneinfo.ZoneInfo("UTC"))  # ensure UTC

        # Convert to ISO string with Z
        now_iso = now_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # Build old version dict (close current version)
        old_data: Dict[str, Any] = dict(current_data)
        old_data["valid_to"] = now_iso
        old_data["is_current"] = False
        old_data["updated_at"] = now_iso

        # Build new version dict (open new version)
        new_data: Dict[str, Any] = {}
        for key, value in current_data.items():
            if key not in cls.SYSTEM_FIELDS:
                new_data[key] = value
        
        new_data["valid_from"] = now_iso
        new_data["valid_to"] = None
        new_data["is_current"] = True
        new_data["created_at"] = now_iso
        new_data["updated_at"] = now_iso

        return {
            "old_data": old_data,
            "new_data": new_data,
            "transition_time": now_iso
        }

    @classmethod
    def update_entity(
        cls, model_class: type[Model], entity_uid: str, update_data: Dict[str, Any]
    ) -> Model:
        """
        Updates an entity using SCD2 mechanism.

        Args:
            model_class: Django model class
            entity_uid: Unique entity identifier (can be UUID string or ForeignKey value)
            update_data: Data to update (without system fields)

        Returns:
            Updated model (new record)

        Raises:
            ValueError: If model doesn't support SCD2 or data is invalid
        """
        # Check that model has required system fields
        cls._validate_model_supports_scd2(model_class)

        # Check that update data doesn't contain system fields
        cls._validate_update_data(update_data)

        # Extract detail_type_id for EntityDetail models
        detail_type_id = update_data.get("detail_type_id") if hasattr(model_class, "entity") else None

        # Execute operation in transaction
        with transaction.atomic():
            # Find current record
            current_record = cls._get_current_record(model_class, entity_uid, detail_type_id)

            if not current_record:
                raise ValueError(f"Entity with identifier {entity_uid} not found")

            # Close current record
            cls._close_current_record(current_record)

            # Create new record
            new_record = cls._create_new_record(
                model_class, entity_uid, update_data, current_record
            )

            return new_record

    @classmethod
    def create_new_version(
        cls, model_class: type[Model], data: Dict[str, Any]
    ) -> Model:
        """
        Creates a new version of an entity (for new records).

        Args:
            model_class: Django model class
            data: Data for the new record

        Returns:
            Created model instance
        """
        now = timezone.now()

        # Prepare data for new record
        new_record_data = {
            "valid_from": now,
            "valid_to": None,
            "is_current": True,
            "created_at": now,
            "updated_at": now,
        }

        # Add provided data
        new_record_data.update(data)

        # Create new record
        new_record = model_class(**new_record_data)
        new_record.save()

        return new_record

    @classmethod
    def _validate_model_supports_scd2(cls, model_class: type[Model]) -> None:
        """Validates that model supports SCD2."""
        model_fields = {field.name for field in model_class._meta.get_fields()}

        missing_fields = cls.SYSTEM_FIELDS - model_fields
        if missing_fields:
            raise ValueError(
                f"Model {model_class.__name__} does not support SCD2. "
                f"Missing fields: {missing_fields}"
            )

    @classmethod
    def _validate_update_data(cls, update_data: Dict[str, Any]) -> None:
        """Validates that update data doesn't contain system fields."""
        invalid_fields = cls.SYSTEM_FIELDS.intersection(update_data.keys())
        if invalid_fields:
            raise ValueError(
                f"Cannot update system fields: {invalid_fields}. "
                f"System fields are managed automatically by SCD2."
            )

    @classmethod
    def _get_current_record(
        cls, model_class: type[Model], entity_uid: str, detail_type_id: str = None
    ) -> Optional[Model]:
        """Finds current record for entity_uid or entity ForeignKey."""
        try:
            # Check if model has entity_uid field (like Entity)
            if hasattr(model_class, "entity_uid"):
                return model_class.objects.get(entity_uid=entity_uid, is_current=True)
            # Check if model has entity ForeignKey (like EntityDetail)
            elif hasattr(model_class, "entity"):
                if detail_type_id:
                    # For EntityDetail, need both entity and detail_type
                    return model_class.objects.get(
                        entity_id=entity_uid,
                        detail_type_id=detail_type_id,
                        is_current=True,
                    )
                else:
                    # Fallback to just entity_id
                    return model_class.objects.get(
                        entity_id=entity_uid, is_current=True
                    )
            else:
                raise ValueError(
                    f"Model {model_class.__name__} doesn't have entity_uid or entity field"
                )
        except model_class.DoesNotExist:
            return None

    @classmethod
    def _close_current_record(cls, current_record: Model) -> None:
        """Closes current record by setting valid_to and is_current=False."""
        now = timezone.now()

        # Update system fields
        current_record.valid_to = now
        current_record.is_current = False
        current_record.updated_at = now

        # Save changes
        current_record.save(update_fields=["valid_to", "is_current", "updated_at"])

    @classmethod
    def _create_new_record(
        cls,
        model_class: type[Model],
        entity_uid: str,
        update_data: Dict[str, Any],
        current_record: Model,
    ) -> Model:
        """Creates new record with updated data."""
        now = timezone.now()

        # Prepare data for new record
        new_record_data = {
            "valid_from": now,
            "valid_to": None,
            "is_current": True,
            "created_at": now,
            "updated_at": now,
        }

        # Add entity identifier based on model type
        if hasattr(model_class, "entity_uid"):
            new_record_data["entity_uid"] = entity_uid
        elif hasattr(model_class, "entity"):
            new_record_data["entity_id"] = entity_uid

        # Add update data (filter out relation fields)
        filtered_update_data = {
            k: v
            for k, v in update_data.items()
            if not k.endswith("_set") and k != "details"
        }
        new_record_data.update(filtered_update_data)

        # Copy fields from current record that weren't updated
        for field in model_class._meta.get_fields():
            if (
                field.name not in new_record_data
                and field.name not in cls.SYSTEM_FIELDS
                and field.name != "id"
                and not field.is_relation  # Skip reverse relations
                and hasattr(current_record, field.name)
            ):
                new_record_data[field.name] = getattr(current_record, field.name)

        # Create new record
        new_record = model_class(**new_record_data)
        new_record.save()

        return new_record
