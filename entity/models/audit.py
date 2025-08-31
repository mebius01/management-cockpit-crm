from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import uuid


class AuditLog(models.Model):
    """
    Centralized audit log for tracking all changes to entities and details.
    Stores complete history of who, when, and what changed.
    """
    
    audit_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    actor = models.ForeignKey(User, on_delete=models.PROTECT, help_text="User that initiated the change")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    entity_uid = models.UUIDField(db_index=True, help_text="Entity identifier that was changed")
    
    table_name = models.CharField(max_length=50, db_index=True, help_text="Table that was modified (entity, entity_detail)")
    operation = models.CharField(max_length=10, choices=[
        ('INSERT', 'Insert'),
        ('UPDATE', 'Update'), 
        ('DELETE', 'Delete'),
    ], db_index=True)
    
    detail_code = models.CharField(max_length=100, null=True, blank=True, db_index=True, 
                                 help_text="Detail type code for detail changes")
    
    before_value = models.JSONField(null=True, blank=True, help_text="Value before change")
    after_value = models.JSONField(null=True, blank=True, help_text="Value after change")
    
    request_id = models.UUIDField(null=True, blank=True, help_text="Request identifier for grouping related changes")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = "audit_log"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['entity_uid', 'timestamp'], name='audit_entity_time_idx'),
            models.Index(fields=['actor', 'timestamp'], name='audit_actor_time_idx'),
            models.Index(fields=['table_name', 'operation'], name='audit_table_op_idx'),
            models.Index(fields=['detail_code'], name='audit_detail_code_idx'),
            models.Index(fields=['request_id'], name='audit_request_idx'),
        ]
        
    def __str__(self):
        return f"{self.operation} on {self.table_name} by {self.actor.username} at {self.timestamp}"
