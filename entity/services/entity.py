from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
from typing import Dict, Any, Optional
from entity.models import Entity
from services.audit import AuditService
from services.scd2 import SCD2Service
from entity.middleware import AuditContext
from entity.serializers import EntityRWSerializer, EntitySerializer
from entity.models import EntityDetail
from services.hash import HashService


class EntityService:
    """
    Service layer for Entity business logic including SCD2 operations and audit logging.
    Uses SCD2Service for updates and direct model creation for new entities.
    """

    @classmethod
    @transaction.atomic
    def create_entity(
        cls, entity_data: Dict[str, Any], user: Optional[User] = None
    ) -> Entity:
        """
        Create a new entity with initial SCD2 fields and audit logging.

        Args:
            entity_data: Dictionary containing validated entity fields
            user: User creating the entity (for audit logging)

        Returns:
            Created Entity instance
        """
        # Extract input_details if present (handled separately)
        input_details = entity_data.pop("input_details", [])

        # Create entity with proper hashdiff calculation
        entity = Entity(**entity_data)
        entity.apply_save()

        # Create associated details if provided
        if input_details:
            for detail_data in input_details:
                detail_kwargs = {
                    "entity": entity,
                    "detail_type": detail_data["detail_type"],
                    "detail_value": detail_data["detail_value"],
                }
                if detail_data.get("valid_from"):
                    detail_kwargs["valid_from"] = detail_data["valid_from"]
                
                EntityDetail.objects.create(**detail_kwargs)

        # Log entity creation if user is provided
        if user and user.is_authenticated:
            cls._log_entity_creation(entity, user)

        return entity

    @classmethod
    @transaction.atomic
    def update_entity(
        cls,
        entity_uid: str,
        update_data: Dict[str, Any],
        user: Optional[User],
        current_entity_hash: str,
    ) -> Optional[Dict[str, Any]]:
        """Update an entity with SCD2 semantics.

        Returns None if the normalized hash of the would-be-updated entity
        equals the current hash (idempotent/no-op).
        """

        new_display_name = update_data.get("display_name")
        new_entity_type = update_data.get("entity_type")
        new_entity_type_id = (
            getattr(new_entity_type, "code", new_entity_type)
            if new_entity_type
            else None
        )

        # Idempotency check against current hash
        if HashService.compare_raw_to_hash(
            current_entity_hash, [new_display_name, new_entity_type_id]
        ):
            return None

        entity = Entity.objects.get(entity_uid=entity_uid, is_current=True)
        current_entity_data = EntitySerializer(entity).data
        upd_data = SCD2Service.build_version_transition(current_entity_data)
        
        # Log entity update if user is provided
        if user and user.is_authenticated:
            cls._log_entity_update(entity, user, current_entity_data)
        
        # Close current version first
        entity.valid_to = timezone.now()
        entity.is_current = False
        entity.updated_at = timezone.now()
        entity.save()
        
        # Create new version
        cls.create_entity(
            {
                **update_data,
                "entity_uid": entity_uid,
            },
            user,
        )
        return upd_data

    @classmethod
    def _log_entity_creation(cls, entity: Entity, user: User) -> None:
        """
        Log entity creation to audit trail.

        Args:
            entity: Created entity
            user: User who created the entity
        """
        AuditService.log_entity_change(
            entity_uid=str(entity.entity_uid),
            operation="INSERT",
            user=user,
            before_data=None,
            after_data={
                "display_name": entity.display_name,
                "entity_type_id": entity.entity_type_id,
            },
            request_context=AuditContext.get_context(),
        )

    @classmethod
    def _log_entity_update(
        cls,
        entity: Entity,
        user: User,
        before_data: Dict[str, Any],
    ) -> None:
        """
        Log entity update to audit trail.

        Args:
            entity: Entity that was updated
            user: User who updated the entity
            before_data: Entity state before update
        """
        after_data = {
            "display_name": entity.display_name,
            "entity_type_id": entity.entity_type_id,
        }

        AuditService.log_entity_change(
            entity_uid=str(entity.entity_uid),
            operation="UPDATE",
            user=user,
            before_data=before_data,
            after_data=after_data,
            request_context=AuditContext.get_context(),
        )
