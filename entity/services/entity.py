from django.db import transaction
from django.contrib.auth.models import User
from typing import Dict, Any, Optional
from entity.models import Entity
from services.audit import AuditService
from entity.middleware import AuditContext


class EntityService:
    """
    Service layer for Entity business logic including audit logging.
    Separates business logic from view layer.
    """
    
    @classmethod
    @transaction.atomic
    def create_entity(cls, entity_data: Dict[str, Any], user: Optional[User] = None) -> Entity:
        """
        Create a new entity with audit logging.
        
        Args:
            entity_data: Dictionary containing entity fields
            user: User creating the entity (for audit logging)
            
        Returns:
            Created Entity instance
        """
        from entity.serializers import EntityRWSerializer
        
        # Create entity using serializer
        serializer = EntityRWSerializer(data=entity_data)
        serializer.is_valid(raise_exception=True)
        entity = serializer.save()
        
        # Log entity creation if user is provided
        if user and user.is_authenticated:
            cls._log_entity_creation(entity, user)
            
        return entity
    
    @classmethod
    @transaction.atomic
    def update_entity(cls, entity: Entity, update_data: Dict[str, Any], user: Optional[User] = None) -> Entity:
        """
        Update an existing entity with audit logging.
        
        Args:
            entity: Entity instance to update
            update_data: Dictionary containing updated fields
            user: User updating the entity (for audit logging)
            
        Returns:
            Updated Entity instance
        """
        from entity.serializers import EntityRWSerializer
        
        # Capture before state for audit
        before_data = None
        if user and user.is_authenticated:
            before_data = {
                'display_name': entity.display_name,
                'entity_type_id': entity.entity_type_id
            }
        
        # Update entity using serializer
        serializer = EntityRWSerializer(entity, data=update_data)
        serializer.is_valid(raise_exception=True)
        updated_entity = serializer.save()
        
        # Log entity update if user is provided
        if user and user.is_authenticated:
            cls._log_entity_update(entity, update_data, user, before_data)
            
        return updated_entity
    
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
        # Compare and log changes
        changes = AuditService.compare_entity_data(entity, update_data)
        if changes:
            AuditService.log_entity_change(
                entity_uid=str(entity.entity_uid),
                operation='UPDATE',
                user=user,
                before_data=changes.get('before'),
                after_data=changes.get('after'),
                request_context=AuditContext.get_context()
            )