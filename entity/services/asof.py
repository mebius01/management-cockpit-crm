from typing import List, Dict, Any, Optional
from datetime import datetime
from django.db.models import Q
from entity.models import Entity, EntityDetail


class AsOfService:
    """Service for retrieving entity state at specific point in time."""
    
    @staticmethod
    def get_entities_as_of(as_of_date: datetime) -> List[Dict[str, Any]]:
        """
        Get all entities and their details as they existed at the specified date.
        
        Args:
            as_of_date: The date to query state for
            
        Returns:
            List of entity snapshots with their details
        """
        entities_snapshot = []
        
        # Get all entities that were valid at the as_of_date
        entities = Entity.objects.filter(
            Q(valid_from__lte=as_of_date) & 
            (Q(valid_to__isnull=True) | Q(valid_to__gt=as_of_date))
        ).select_related('entity_type')
        
        for entity in entities:
            # Get details that were valid at the as_of_date for this entity
            details = EntityDetail.objects.filter(
                entity__entity_uid=entity.entity_uid,
                valid_from__lte=as_of_date
            ).filter(
                Q(valid_to__isnull=True) | Q(valid_to__gt=as_of_date)
            ).select_related('detail_type')
            
            entity_snapshot = {
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
                    for detail in details
                ]
            }
            entities_snapshot.append(entity_snapshot)
        
        return entities_snapshot
    
    @staticmethod
    def get_entity_as_of(entity_uid: str, as_of_date: datetime) -> Optional[Dict[str, Any]]:
        """
        Get specific entity and its details as they existed at the specified date.
        
        Args:
            entity_uid: UUID of the entity
            as_of_date: The date to query state for
            
        Returns:
            Entity snapshot with details or None if not found
        """
        try:
            # Get entity version that was valid at the as_of_date
            entity = Entity.objects.filter(
                entity_uid=entity_uid,
                valid_from__lte=as_of_date
            ).filter(
                Q(valid_to__isnull=True) | Q(valid_to__gt=as_of_date)
            ).select_related('entity_type').first()
            
            if not entity:
                return None
            
            # Get details that were valid at the as_of_date
            details = EntityDetail.objects.filter(
                entity__entity_uid=entity_uid,
                valid_from__lte=as_of_date
            ).filter(
                Q(valid_to__isnull=True) | Q(valid_to__gt=as_of_date)
            ).select_related('detail_type')
            
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
                    for detail in details
                ]
            }
        except Entity.DoesNotExist:
            return None
