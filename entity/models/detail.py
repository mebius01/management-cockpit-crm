from typing import Any

from django.contrib.postgres.constraints import ExclusionConstraint
from django.db import models
from django.db.models import F, Func, Q, UniqueConstraint, Value
from django.utils import timezone

from services.hash import HashService

from .entity import Entity
from .type import DetailType


class EntityDetail(models.Model):
    """
    Stores versioned details for an entity.
    """
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='details')
    detail_type = models.ForeignKey(DetailType, on_delete=models.CASCADE)
    detail_value = models.TextField()
    hashdiff = models.CharField(max_length=64, editable=False)

    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-valid_from']
        indexes = [
            # Covering indexes for common query patterns
            models.Index(
                fields=['entity', 'is_current'],
                include=['detail_type', 'detail_value', 'valid_from'],
                name='det_ent_curr_cov_idx'
            ),
            models.Index(
                fields=['entity', 'detail_type', 'is_current'],
                include=['detail_value', 'valid_from'],
                name='det_ent_type_curr_cov_idx'
            ),
            models.Index(
                fields=['entity', 'valid_from'],
                include=['detail_type', 'detail_value', 'is_current'],
                name='det_ent_valid_from_cov_idx'
            ),
            models.Index(
                fields=['detail_type', 'is_current'],
                include=['entity', 'detail_value', 'valid_from'],
                name='det_type_curr_cov_idx'
            ),
            models.Index(
                fields=['hashdiff'],
                include=['entity', 'detail_type', 'detail_value'],
                name='det_hashdiff_cov_idx'),
        ]
        constraints = [
            UniqueConstraint(
                fields=['entity', 'detail_type'],
                condition=Q(is_current=True),
                name='unique_current_entity_detail'
            ),
            ExclusionConstraint(
                name='exclude_overlapping_details',
                expressions=[
                    (F('entity_id'), '='),
                    (F('detail_type_id'), '='),
                    (Func(
                        F('valid_from'),
                        F('valid_to'),
                        Value('[)'),
                        function='tstzrange'),
                    '&&')
                ],
            ),
        ]


    def __str__(self) -> str:
        return f"{self.detail_type.code}: {self.detail_value}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        components = [self.detail_value, str(self.detail_type.code)]
        self.hashdiff = HashService.compute(components)
        super().save(*args, **kwargs)

