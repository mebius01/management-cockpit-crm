from typing import Any

from django.db.models.fields import UUIDField

from entity.models import Entity, EntityDetail


class HistoryService:
    """Service for retrieving combined historical data for entities."""

    @staticmethod
    def get_combined_history(entity_uid: UUIDField) -> list[dict[str, Any]]:
        """Get chronological history of Entity and EntityDetail changes."""
        history_entries = []

        # Optimized: single query with proper ordering at DB level
        entity_versions = Entity.objects.filter(
            entity_uid=entity_uid
        ).select_related('entity_type').order_by('valid_from')

        detail_versions = EntityDetail.objects.filter(
            entity__entity_uid=entity_uid
        ).select_related('entity', 'detail_type').order_by('valid_from')

        for entity in entity_versions:
            history_entries.append({
                'type': 'entity',
                'valid_from': entity.valid_from,
                'valid_to': entity.valid_to,
                'is_current': entity.is_current,
                'created_at': entity.created_at,
                'updated_at': entity.updated_at,
                'changes': {
                    'display_name': entity.display_name,
                    'entity_type': entity.entity_type.code if entity.entity_type else None,
                },
                'hashdiff': entity.hashdiff,
                'entity_uid': entity.entity_uid,
            })

        for detail in detail_versions:
            history_entries.append({
                'type': 'detail',
                'valid_from': detail.valid_from,
                'valid_to': detail.valid_to,
                'is_current': detail.is_current,
                'created_at': detail.created_at,
                'updated_at': detail.updated_at,
                'changes': {
                    'detail_type': detail.detail_type.code if detail.detail_type else None,
                    'detail_value': detail.detail_value,
                },
                'hashdiff': detail.hashdiff,
                'entity_uid': detail.entity.entity_uid,
            })

        # Sort merged results chronologically
        history_entries.sort(key=lambda x: x['valid_from'])
        return history_entries
