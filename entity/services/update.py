from django.db import transaction
from django.utils import timezone
from datetime import datetime
from typing import Dict, Any, Optional
from entity.models import Entity, EntityDetail
from entity.services.datetime_validation import DateTimeValidationService
import hashlib
import logging

logger = logging.getLogger(__name__)


class UpdateService:
    @staticmethod
    def _compute_entity_hashdiff(display_name: str, entity_type_id: int) -> str:
        """Compute hashdiff for entity data for idempotency checks."""
        normalized_name = display_name.strip().lower()
        normalized_type = str(entity_type_id)
        combined = f"{normalized_name}|{normalized_type}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

    @staticmethod
    def _compute_detail_hashdiff(detail_value: str) -> str:
        """Compute hashdiff for detail data for idempotency checks."""
        normalized = detail_value.strip().lower()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    @staticmethod
    def _is_entity_change_needed(current_entity: Entity, payload: Dict[str, Any]) -> bool:
        """Check if entity update is needed based on hashdiff comparison."""
        new_display_name = payload.get("display_name", current_entity.display_name)
        new_entity_type = payload.get("entity_type", current_entity.entity_type)
        new_entity_type_id = new_entity_type.id if hasattr(new_entity_type, 'id') else new_entity_type.pk

        new_hashdiff = UpdateService._compute_entity_hashdiff(new_display_name, new_entity_type_id)
        return current_entity.hashdiff != new_hashdiff

    @staticmethod
    def _is_detail_change_needed(current_detail: Optional[EntityDetail], new_value: str) -> bool:
        """Check if detail update is needed based on hashdiff comparison."""
        if not current_detail:
            return True
        new_hashdiff = UpdateService._compute_detail_hashdiff(new_value)
        return current_detail.hashdiff != new_hashdiff

    @staticmethod
    def _close_current_entity(current_entity: Entity, new_valid_from: datetime):
        """Close current entity version."""
        current_entity.valid_to = new_valid_from
        current_entity.is_current = False
        current_entity.save()

    @staticmethod
    def _create_new_entity(current_entity: Entity, payload: Dict[str, Any], new_valid_from: datetime) -> Entity:
        """Create new entity version."""
        return Entity.objects.create(
            entity_uid=current_entity.entity_uid,
            display_name=payload.get("display_name", current_entity.display_name),
            entity_type=payload.get("entity_type", current_entity.entity_type),
            valid_from=new_valid_from,
            is_current=True,
        )

    @staticmethod
    def _update_details(current_entity: Entity, new_entity: Entity, payload: Dict[str, Any], new_valid_from: datetime):
        """Update entity details with idempotency checks."""
        for d in payload.get("details", []):
            dt = d["detail_type"]
            val = d["detail_value"]

            # Get current detail if exists
            try:
                current_detail = EntityDetail.objects.get(
                    entity=current_entity, detail_type=dt, is_current=True
                )
            except EntityDetail.DoesNotExist:
                current_detail = None

            # Check if change is needed
            if UpdateService._is_detail_change_needed(current_detail, val):
                # Close current detail if exists
                if current_detail:
                    current_detail.valid_to = new_valid_from
                    current_detail.is_current = False
                    current_detail.save()

                # Create new detail version
                EntityDetail.objects.create(
                    entity=new_entity,
                    detail_type=dt,
                    detail_value=val,
                    valid_from=new_valid_from,
                    is_current=True,
                )

    @staticmethod
    @transaction.atomic
    def update_entity_idempotent(entity_uid: str, payload: Dict[str, Any], change_ts: Optional[datetime] = None, actor=None) -> tuple[Entity, bool]:
        """
        Idempotent entity update. Returns (entity, was_changed).
        Identical payloads at the same change_ts create no new versions.
        """
        try:
            current = Entity.objects.get(entity_uid=entity_uid, is_current=True)
        except Entity.DoesNotExist:
            raise ValueError(f"Entity with uid {entity_uid} not found")

        # Parse and validate change timestamp
        if change_ts:
            new_valid_from = DateTimeValidationService.parse_datetime(change_ts)
        else:
            new_valid_from = timezone.now()

        # Check if entity change is needed
        entity_needs_update = UpdateService._is_entity_change_needed(current, payload)

        # Check if any detail changes are needed
        details_need_update = False
        for d in payload.get("details", []):
            try:
                current_detail = EntityDetail.objects.get(
                    entity=current, detail_type=d["detail_type"], is_current=True
                )
            except EntityDetail.DoesNotExist:
                current_detail = None

            if UpdateService._is_detail_change_needed(current_detail, d["detail_value"]):
                details_need_update = True
                break

        # If no changes needed, return current entity
        if not entity_needs_update and not details_need_update:
            try:
                actor_id = getattr(actor, 'id', None)
                actor_repr = str(actor) if actor_id else 'anonymous'
                logger.info(
                    "audit.entity.update.noop",
                    extra={
                        "actor": actor_repr,
                        "actor_id": actor_id,
                        "entity_uid": str(current.entity_uid),
                        "change_ts": new_valid_from.isoformat(),
                    },
                )
            except Exception:
                logger.debug("audit logging for update noop failed", exc_info=True)
            return current, False

        # Perform transactional close-and-open
        UpdateService._close_current_entity(current, new_valid_from)
        new_entity = UpdateService._create_new_entity(current, payload, new_valid_from)
        UpdateService._update_details(current, new_entity, payload, new_valid_from)

        try:
            actor_id = getattr(actor, 'id', None)
            actor_repr = str(actor) if actor_id else 'anonymous'
            logger.info(
                "audit.entity.update",
                extra={
                    "actor": actor_repr,
                    "actor_id": actor_id,
                    "entity_uid": str(new_entity.entity_uid),
                    "valid_from": new_valid_from.isoformat(),
                    "details_count": len(payload.get("details", [])),
                },
            )
        except Exception:
            logger.debug("audit logging for update failed", exc_info=True)
        return new_entity, True

    @staticmethod
    @transaction.atomic
    def update_entity(entity_uid: str, payload: Dict[str, Any], actor=None) -> Entity | None:
        """Legacy update method for backward compatibility."""
        try:
            entity, _ = UpdateService.update_entity_idempotent(entity_uid, payload, actor=actor)
            return entity
        except ValueError:
            return None