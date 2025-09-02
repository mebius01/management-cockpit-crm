from datetime import datetime
from typing import Any

from django.db.models import Prefetch, Q, QuerySet

from entity.models import Entity, EntityDetail


class AsOfService:
    """Service for retrieving entity state at specific point in time."""

    @staticmethod
    def get_entities_as_of(as_of_date: datetime) -> QuerySet[Entity]:
        """
        Get all entities and their details as they existed at the specified date.

        Args:
            as_of_date: The date to query state for

        Returns:
            QuerySet of Entity objects with prefetched valid details
        """
        # Optimized query with prefetch_related to avoid N+1 problem
        details_filter = Q(valid_from__lte=as_of_date) & (Q(valid_to__isnull=True) | Q(valid_to__gt=as_of_date))

        return Entity.objects.filter(
            Q(valid_from__lte=as_of_date) &
            (Q(valid_to__isnull=True) | Q(valid_to__gt=as_of_date))
        ).select_related('entity_type').prefetch_related(
            Prefetch(
                'details',
                queryset=EntityDetail.objects.filter(details_filter).select_related('detail_type'),
                to_attr='valid_details'
            )
        )

    @staticmethod
    def get_entity_as_of(entity_uid: str, as_of_date: datetime) -> dict[str, Any] | None:
        """
        Get specific entity and its details as they existed at the specified date.

        Args:
            entity_uid: UUID of the entity
            as_of_date: The date to query state for

        Returns:
            Entity snapshot with details or None if not found
        """
        try:
            # Optimized query with prefetch_related to avoid N+1 problem
            details_filter = Q(valid_from__lte=as_of_date) & (Q(valid_to__isnull=True) | Q(valid_to__gt=as_of_date))

            entity = Entity.objects.filter(
                entity_uid=entity_uid,
                valid_from__lte=as_of_date
            ).filter(
                Q(valid_to__isnull=True) | Q(valid_to__gt=as_of_date)
            ).select_related('entity_type').prefetch_related(
                Prefetch(
                    'details',
                    queryset=EntityDetail.objects.filter(details_filter).select_related('detail_type'),
                    to_attr='valid_details'
                )
            ).first()

            if not entity:
                return None

            return {
                'entity_uid': entity.entity_uid,
                'display_name': entity.display_name,
                'entity_type': entity.entity_type.code if entity.entity_type else None,
                'valid_from': entity.valid_from,
                'valid_to': entity.valid_to,
                'hashdiff': entity.hashdiff,
                'details': [
                    {
                        'detail_type': detail.detail_type.code if detail.detail_type else None,
                        'detail_value': detail.detail_value,
                        'valid_from': detail.valid_from,
                        'valid_to': detail.valid_to,
                        'hashdiff': detail.hashdiff,
                    }
                    for detail in entity.valid_details
                ]
            }
        except Entity.DoesNotExist:
            return None
