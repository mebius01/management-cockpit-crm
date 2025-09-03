from datetime import datetime
from typing import Any, Optional
from collections import defaultdict

from django.db.models import Q

from entity.models.audit import AuditLog


class DiffService:
    """Service for comparing entity states between two points in time using AuditLog."""

    @staticmethod
    def get_entities_diff(from_date: datetime, to_date: datetime) -> list[dict[str, Any]]:
        """
        Get changes in all entities between two dates using AuditLog.

        Args:
            from_date: Start date for comparison
            to_date: End date for comparison

        Returns:
            List of changes grouped by entity_uid
        """
        # Get all audit log entries in the date range with optimized query
        audit_entries = AuditLog.objects.filter(
            timestamp__gte=from_date,
            timestamp__lte=to_date
        ).select_related('actor').order_by('entity_uid', 'timestamp')

        # Group changes by entity_uid
        entity_changes = defaultdict(list)
        
        for entry in audit_entries:
            changes = DiffService._extract_changes_from_audit_entry(entry)
            entity_changes[str(entry.entity_uid)].extend(changes)

        # Convert to required format
        result = []
        for entity_uid, changes in entity_changes.items():
            if changes:  # Only include entities with actual changes
                result.append({
                    'entity_uid': entity_uid,
                    'changes': changes
                })

        return result

    @staticmethod
    def _extract_changes_from_audit_entry(entry: AuditLog) -> list[dict[str, Any]]:
        """
        Extract field changes from a single audit log entry.
        
        Args:
            entry: AuditLog entry
            
        Returns:
            List of field changes
        """
        changes = []
        
        if entry.operation == 'INSERT':
            # For INSERT operations, all fields are new
            if entry.after_value:
                for field, value in entry.after_value.items():
                    changes.append({
                        'field': field,
                        'before': None,
                        'after': value,
                        'change_timestamp': entry.timestamp
                    })
        
        elif entry.operation == 'UPDATE':
            # For UPDATE operations, compare before and after values
            before_value = entry.before_value or {}
            after_value = entry.after_value or {}
            
            # Get all fields that were present in either before or after
            all_fields = set(before_value.keys()) | set(after_value.keys())
            
            for field in all_fields:
                before_val = before_value.get(field)
                after_val = after_value.get(field)
                
                # Only include if values actually changed
                if before_val != after_val:
                    changes.append({
                        'field': field,
                        'before': before_val,
                        'after': after_val,
                        'change_timestamp': entry.timestamp
                    })
        
        elif entry.operation == 'DELETE':
            # For DELETE operations, all fields are removed
            if entry.before_value:
                for field, value in entry.before_value.items():
                    changes.append({
                        'field': field,
                        'before': value,
                        'after': None,
                        'change_timestamp': entry.timestamp
                    })
        
        return changes

    @staticmethod
    def get_entity_diff(entity_uid: str, from_date: datetime, to_date: datetime) -> list[dict[str, Any]]:
        """
        Get changes for specific entity between two dates using AuditLog.

        Args:
            entity_uid: UUID of the entity
            from_date: Start date for comparison
            to_date: End date for comparison

        Returns:
            List of changes for this entity
        """
        # Get audit log entries for specific entity in the date range
        audit_entries = AuditLog.objects.filter(
            entity_uid=entity_uid,
            timestamp__gte=from_date,
            timestamp__lte=to_date
        ).select_related('actor').order_by('timestamp')

        changes = []
        for entry in audit_entries:
            changes.extend(DiffService._extract_changes_from_audit_entry(entry))

        return [{
            'entity_uid': entity_uid,
            'changes': changes
        }] if changes else []
