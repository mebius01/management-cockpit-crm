from django.db import transaction
from django.contrib.auth.models import User
from typing import Dict, Any, Optional
from entity.models import Entity
from services.audit import AuditService
from services.scd2 import SCD2Service
from entity.middleware import AuditContext
from entity.serializers import EntityRWSerializer


class EntityService:
    """
    Service layer for Entity business logic including SCD2 operations and audit logging.
    Uses SCD2Service for updates and direct model creation for new entities.
    """
    
    @classmethod
    @transaction.atomic
    def create_entity(cls, entity_data: Dict[str, Any], user: Optional[User] = None) -> Entity:
        """
        Create a new entity with initial SCD2 fields and audit logging.
        
        Args:
            entity_data: Dictionary containing validated entity fields
            user: User creating the entity (for audit logging)
            
        Returns:
            Created Entity instance
        """
        # Extract input_details if present (handled separately)
        input_details = entity_data.pop('input_details', [])
        
        # Create entity directly with validated data (SCD2 fields set by model defaults)
        entity = Entity(**entity_data)
        entity.save()
        
        # Create associated details if provided
        if input_details:
            from entity.models import EntityDetail
            for detail_data in input_details:
                detail_kwargs = {
                    'entity': entity,
                    'detail_type': detail_data['detail_type'],
                    'detail_value': detail_data['detail_value'],
                }
                if detail_data.get('valid_from'):
                    detail_kwargs['valid_from'] = detail_data['valid_from']
                EntityDetail.objects.create(**detail_kwargs)
        
        # Log entity creation if user is provided
        if user and user.is_authenticated:
            cls._log_entity_creation(entity, user)
            
        return entity
    
    @classmethod
    @transaction.atomic
    def update_entity(cls, entity_uid: str, update_data: Dict[str, Any], user: Optional[User] = None) -> Entity:
        """
        Update an existing entity using SCD2 close-and-open logic with audit logging.
        
        Args:
            entity_uid: UUID of the entity to update
            update_data: Dictionary containing updated fields
            user: User updating the entity (for audit logging)
            
        Returns:
            New current Entity instance
        """
        # Extract input_details if present (handled separately)
        input_details = update_data.pop('input_details', [])
        
        # Get current entity for audit logging
        current_entity = None
        before_data = None
        if user and user.is_authenticated:
            current_entity = SCD2Service.get_current_record(Entity, 'entity_uid', entity_uid)
            if current_entity:
                before_data = {
                    'display_name': current_entity.display_name,
                    'entity_type_id': current_entity.entity_type_id
                }
        
        # Update entity using SCD2Service
        updated_entity = SCD2Service.update_record(
            model_class=Entity,
            uid_field='entity_uid',
            uid_value=entity_uid,
            data=update_data
        )
        
        # Always handle EntityDetail records for SCD2 consistency
        from entity.models import EntityDetail
        
        # Get current details before closing them
        current_details = EntityDetail.objects.filter(
            entity__entity_uid=entity_uid,
            is_current=True
        ).select_related('detail_type')
        
        # Close current details for this entity
        current_details.update(
            valid_to=updated_entity.valid_from,
            is_current=False
        )
        
        if input_details:
            # Create new detail records from input_details
            for detail_data in input_details:
                detail_kwargs = {
                    'entity': updated_entity,
                    'detail_type': detail_data['detail_type'],
                    'detail_value': detail_data['detail_value'],
                    'valid_from': updated_entity.valid_from,
                    'valid_to': None,
                    'is_current': True
                }
                if detail_data.get('valid_from'):
                    detail_kwargs['valid_from'] = detail_data['valid_from']
                EntityDetail.objects.create(**detail_kwargs)
        else:
            # Copy existing details to maintain SCD2 consistency
            for detail in current_details:
                EntityDetail.objects.create(
                    entity=updated_entity,
                    detail_type=detail.detail_type,
                    detail_value=detail.detail_value,
                    valid_from=updated_entity.valid_from,
                    valid_to=None,
                    is_current=True
                )
        
        # Log entity update if user is provided and entity actually changed
        if user and user.is_authenticated and current_entity and updated_entity.id != current_entity.id:
            cls._log_entity_update(updated_entity, update_data, user, before_data)
            
        return updated_entity
    
    @classmethod
    def get_current_entity(cls, entity_uid: str) -> Optional[Entity]:
        """
        Get the current version of an entity.
        
        Args:
            entity_uid: UUID of the entity
            
        Returns:
            Current Entity instance or None if not found
        """
        return SCD2Service.get_current_record(Entity, 'entity_uid', entity_uid)
    
    @classmethod
    def get_entity_as_of(cls, entity_uid: str, as_of_date) -> Optional[Entity]:
        """
        Get entity version that was current at a specific point in time.
        
        Args:
            entity_uid: UUID of the entity
            as_of_date: Point in time to query
            
        Returns:
            Entity instance that was current at as_of_date or None if not found
        """
        return SCD2Service.get_as_of_record(Entity, 'entity_uid', entity_uid, as_of_date)
    
    @classmethod
    def get_entity_history(cls, entity_uid: str):
        """
        Get complete history of an entity.
        
        Args:
            entity_uid: UUID of the entity
            
        Returns:
            QuerySet of all Entity versions ordered by valid_from desc
        """
        return SCD2Service.get_history(Entity, 'entity_uid', entity_uid)
    
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
            operation='INSERT',
            user=user,
            before_data=None,
            after_data={
                'display_name': entity.display_name,
                'entity_type_id': entity.entity_type_id
            },
            request_context=AuditContext.get_context()
        )
    
    @classmethod
    def _log_entity_update(cls, entity: Entity, update_data: Dict[str, Any], 
                          user: User, before_data: Dict[str, Any]) -> None:
        """
        Log entity update to audit trail.
        
        Args:
            entity: Entity that was updated
            update_data: Data that was used for update
            user: User who updated the entity
            before_data: Entity state before update
        """
        after_data = {
            'display_name': entity.display_name,
            'entity_type_id': entity.entity_type_id
        }
        
        AuditService.log_entity_change(
            entity_uid=str(entity.entity_uid),
            operation='UPDATE',
            user=user,
            before_data=before_data,
            after_data=after_data,
            request_context=AuditContext.get_context()
        )