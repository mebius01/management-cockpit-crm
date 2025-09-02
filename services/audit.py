import uuid
from typing import Any

from django.contrib.auth.models import User
from django.db.models import UUIDField
from django.utils import timezone

from entity.models.audit import AuditLog


class AuditService:
    """
    Centralized service for handling audit logging across all modules.
    Tracks before/after values and creates audit records within transactions.
    """

    @classmethod
    def log_entity_change(cls,
                        entity_uid: UUIDField,
                        operation: str,
                        user: User,
                        before_data: dict[str, Any] | None = None,
                        after_data: dict[str, Any] | None = None,
                        request_context: dict[str, Any] | None = None) -> AuditLog:
        """
        Log changes to Entity table.

        Args:
            entity_uid: UUID of the entity being changed
            operation: INSERT, UPDATE, or DELETE
            user: User object making the change
            before_data: Entity data before change
            after_data: Entity data after change
            request_context: Additional request context (IP, user agent, etc.)
        """
        return cls._create_audit_log(
            entity_uid=entity_uid,
            table_name='entity',
            operation=operation,
            user=user,
            detail_code=None,
            before_data=before_data,
            after_data=after_data,
            request_context=request_context
        )

    @classmethod
    def log_detail_change(cls,
                        entity_uid: UUIDField,
                        operation: str,
                        user: User,
                        before_data: dict[str, Any] | None = None,
                        after_data: dict[str, Any] | None = None,
                        request_context: dict[str, Any] | None = None) -> AuditLog:
        """
        Log changes to EntityDetail table.

        Args:
            entity_uid: UUID of the entity whose detail is changing
            detail_code: Code of the detail type being changed
            operation: INSERT, UPDATE, or DELETE
            user: User object making the change
            before_data: Detail data before change
            after_data: Detail data after change
            request_context: Additional request context
        """
        return cls._create_audit_log(
            entity_uid=entity_uid,
            table_name='entity_detail',
            operation=operation,
            user=user,
            before_data=before_data,
            after_data=after_data,
            request_context=request_context
        )

    @classmethod
    def log_batch_changes(cls,
                         changes: list[dict[str, Any]],
                         request_id: str | None = None) -> list:
        """
        Log multiple changes as a batch with shared request_id.

        Args:
            changes: list of change dictionaries with audit parameters
            request_id: Optional request ID to group related changes
        """
        if not request_id:
            request_id = str(uuid.uuid4())

        audit_logs = []
        for change in changes:
            change['request_context'] = change.get('request_context', {})
            change['request_context']['request_id'] = request_id

            if change.get('detail_code'):
                audit_log = cls.log_detail_change(**change)
            else:
                audit_log = cls.log_entity_change(**change)
            audit_logs.append(audit_log)

        return audit_logs

    @classmethod
    def compare_entity_data(cls, old_entity, new_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """
        Compare old entity with new data to identify changes.

        Returns:
            Dict with 'before' and 'after' keys containing changed fields only
        """
        before = {}
        after = {}

        # Fields to track for entities
        tracked_fields = ['display_name', 'entity_type_id']

        for field in tracked_fields:
            old_value = getattr(old_entity, field, None)
            new_value = new_data.get(field)

            # Handle entity_type special case
            if field == 'entity_type_id' and 'entity_type' in new_data:
                new_value = new_data['entity_type']

            if old_value != new_value:
                before[field] = old_value
                after[field] = new_value

        return {'before': before, 'after': after} if before or after else {}

    @classmethod
    def compare_detail_data(cls, old_detail, new_value: str) -> dict[str, dict[str, Any]]:
        """
        Compare old detail with new value.

        Returns:
            Dict with 'before' and 'after' keys if value changed
        """
        if old_detail.detail_value != new_value:
            return {
                'before': {'detail_value': old_detail.detail_value},
                'after': {'detail_value': new_value}
            }
        return {}

    @classmethod
    def _create_audit_log(cls,
                        entity_uid: UUIDField,
                        table_name: str,
                        operation: str,
                        user: User,
                        detail_code: str | None = None,
                        before_data: dict[str, Any] | None = None,
                        after_data: dict[str, Any] | None = None,
                        request_context: dict[str, Any] | None = None) -> AuditLog:
        """
        Create audit log record with provided parameters.
        """
        from entity.models.audit import AuditLog

        audit_log = AuditLog(
            entity_uid=entity_uid,
            table_name=table_name,
            operation=operation,
            actor=user,
            detail_code=detail_code,
            before_value=before_data,
            after_value=after_data,
            timestamp=timezone.now()
        )

        # Add request context if provided
        if request_context:
            audit_log.request_id = request_context.get('request_id')
            audit_log.ip_address = request_context.get('ip_address')
            audit_log.user_agent = request_context.get('user_agent')

        audit_log.save()
        return audit_log

    @classmethod
    def get_entity_audit_trail(cls, entity_uid: str) -> list:
        """
        Get complete audit trail for an entity.
        """
        from entity.models.audit import AuditLog

        return list(AuditLog.objects.filter(
            entity_uid=entity_uid
        ).select_related('actor').order_by('-timestamp'))

    @classmethod
    def get_user_activity(cls, user: User, limit: int = 100) -> list:
        """
        Get recent activity for a specific user.
        """
        from entity.models.audit import AuditLog

        return list(AuditLog.objects.filter(
            actor=user
        ).select_related('actor').order_by('-timestamp')[:limit])
