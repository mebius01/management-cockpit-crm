from django.db import transaction
from entity.models import Entity, EntityDetail
from entity.serializers import EntitySerializer, EntityDetailSerializer
from django.utils import timezone

class CreateService:
    """Service class for handling entity creation logic."""

    @staticmethod
    @transaction.atomic
    def create_entity(payload: dict):
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
        return {
            "entity": EntitySerializer(entity).data,
            "details": EntityDetailSerializer(entity.details.filter(is_current=True), many=True).data,
        }
