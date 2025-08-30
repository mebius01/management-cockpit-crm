from django.db import models
from django.contrib.postgres.constraints import ExclusionConstraint
from django.db.models import UniqueConstraint, Q, F, Func, Value
from django.utils import timezone
import uuid
import hashlib
from .type import EntityType

class Entity(models.Model):
    """
    Represents a person, institution, or other entity.
    Each row is a version tied to a stable entity_uid.
    """
    entity_uid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    display_name = models.CharField(max_length=255, db_index=True)
    entity_type = models.ForeignKey(EntityType, on_delete=models.PROTECT)
    hashdiff = models.CharField(max_length=64, editable=False)

    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "entity"
        indexes = [
            models.Index(fields=['is_current'], name='entity_is_current_idx'),
            models.Index(fields=['is_current', 'display_name'], name='entity_current_name_idx'),
            # Covering indexes for common query patterns
            models.Index(fields=['entity_uid', 'is_current'], include=['display_name', 'entity_type', 'valid_from'], name='ent_uid_curr_cov_idx'),
            models.Index(fields=['is_current', 'entity_type'], include=['entity_uid', 'display_name', 'valid_from'], name='ent_curr_type_cov_idx'),
            models.Index(fields=['valid_from'], include=['entity_uid', 'display_name', 'entity_type', 'is_current'], name='ent_valid_from_cov_idx'),
            models.Index(fields=['display_name'], include=['entity_uid', 'entity_type', 'is_current', 'valid_from'], name='ent_name_cov_idx'),
        ]
        ordering = ['-valid_from']
        constraints = [
            UniqueConstraint(fields=['entity_uid'], condition=Q(is_current=True), name='unique_current_entity'),
            ExclusionConstraint(
                name='exclude_overlapping_entities',
                expressions=[
                    (F('entity_uid'), '='),
                    (Func(F('valid_from'), F('valid_to'), Value('[)'), function='tstzrange'), '&&')
                ],
            ),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.entity_uid})"

    def save(self, *args, **kwargs):
        # Compute hashdiff from normalized business values for idempotency
        normalized_name = self.display_name.strip().lower()
        normalized_type = str(self.entity_type_id) if self.entity_type_id else ""
        combined = f"{normalized_name}|{normalized_type}"
        self.hashdiff = hashlib.sha256(combined.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)