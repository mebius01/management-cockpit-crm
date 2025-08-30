from datetime import datetime
from typing import Optional, Union

from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from entity.models import Entity, EntityDetail
from django.db.models import Q, Prefetch
from entity.services.datetime_validation import DateTimeValidationService


class AsOfService:
    """Service class for handling entity listing logic as of a certain time."""

    @staticmethod
    def get_queryset(filters: dict):
        as_of = filters.get("as_of")
        if not as_of:
            raise ValueError("'as_of' parameter is required.")
        try:
            as_of = DateTimeValidationService.parse_datetime(as_of)
        except ValueError:
            raise

        details_prefetch = Prefetch(
            'details',
            queryset=EntityDetail.objects.filter(
                Q(valid_from__lte=as_of) & (Q(valid_to__gt=as_of) | Q(valid_to__isnull=True))
            ),
            to_attr='details_as_of'
        )
        return Entity.objects.filter(
            Q(valid_from__lte=as_of) & (Q(valid_to__gt=as_of) | Q(valid_to__isnull=True))
        ).prefetch_related(details_prefetch)

    @staticmethod
    def paginate_queryset(qs, request: Request):
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator, page