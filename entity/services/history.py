from typing import Any, Dict, List

from django.db.models import Q

from entity.models import Entity, EntityDetail


class HistoryService:
    """Service for retrieving combined historical data for entities."""

    @staticmethod
    def get_combined_history(entity_uid: str) -> List[Dict[str, Any]]:
        """
        Get combined chronological history of Entity and EntityDetail changes.

        Args:
            entity_uid: UUID of the entity to get history for

        Returns:
            List of history entries sorted by valid_from (newest first)
        """
        history_entries = []

        # Get all Entity versions for this entity_uid
        entity_versions = Entity.objects.filter(
            entity_uid=entity_uid
        ).select_related('entity_type').order_by('-valid_from')

        for entity in entity_versions:
            history_entries.append({
                'type': 'entity',
                'valid_from': entity.valid_from,
                'valid_to': entity.valid_to,
                'is_current': entity.is_current,
                'changes': {
                    'display_name': entity.display_name,
                    'entity_type': entity.entity_type.code if entity.entity_type else None,
                },
                'hashdiff': entity.hashdiff,
                'entity_uid': entity.entity_uid,
            })

        # Get all EntityDetail versions for this entity_uid
        detail_versions = EntityDetail.objects.filter(
            entity__entity_uid=entity_uid
        ).select_related('entity', 'detail_type').order_by('-valid_from')

        for detail in detail_versions:
            history_entries.append({
                'type': 'detail',
                'valid_from': detail.valid_from,
                'valid_to': detail.valid_to,
                'is_current': detail.is_current,
                'changes': {
                    'detail_type': detail.detail_type.code if detail.detail_type else None,
                    'detail_value': detail.detail_value,
                },
                'hashdiff': detail.hashdiff,
                'entity_uid': detail.entity.entity_uid,
            })

        # Sort all entries by valid_from (newest first)
        history_entries.sort(key=lambda x: x['valid_from'], reverse=True)

        return history_entries
