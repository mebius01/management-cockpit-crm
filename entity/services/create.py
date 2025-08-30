from django.db import transaction
from entity.models import Entity, EntityDetail
from entity.serializers import EntitySerializer, EntityDetailSerializer
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class CreateService:
    """Service class for handling entity creation logic."""

    @staticmethod
    @transaction.atomic
    def create_entity(payload: dict, actor=None):
        """Creates an entity and its details within a single transaction."""
        valid_from = payload.get("valid_from") or timezone.now()
        entity = Entity.objects.create(
            display_name=payload["display_name"],
            entity_type=payload["entity_type"],
            valid_from=valid_from,
            is_current=True,
        )
        for d in payload.get("details", []):
            EntityDetail.objects.create(
                entity=entity,
                detail_type=d["detail_type"],
                detail_value=d["detail_value"],
                valid_from=d.get("valid_from") or valid_from,
                is_current=True,
            )

        # Minimal audit log
        try:
            actor_id = getattr(actor, 'id', None)
            actor_repr = str(actor) if actor_id else 'anonymous'
            logger.info(
                "audit.entity.create",
                extra={
                    "actor": actor_repr,
                    "actor_id": actor_id,
                    "entity_uid": str(entity.entity_uid),
                    "entity_type_id": getattr(entity.entity_type, 'id', None),
                    "valid_from": valid_from.isoformat(),
                    "details_count": len(payload.get("details", [])),
                },
            )
        except Exception:  # logging must never break the main flow
            logger.debug("audit logging for entity create failed", exc_info=True)
        return {
            "entity": EntitySerializer(entity).data,
            "details": EntityDetailSerializer(entity.details.filter(is_current=True), many=True).data,
        }
