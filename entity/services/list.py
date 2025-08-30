from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from entity.models import Entity, EntityDetail
from django.db.models import Q, Prefetch

class ListService:
    """Service class for handling entity listing logic."""
    @staticmethod
    def get_queryset(filters: dict):
        qs = Entity.objects.filter(is_current=True)
        if filters.get('q'):
            qs = qs.filter(display_name__icontains=filters['q'])
        if filters.get('type'):
            qs = qs.filter(entity_type__code=filters['type'])
        return qs.order_by("display_name")

    @staticmethod
    def paginate_queryset(qs, request: Request):
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        return page, paginator

    @staticmethod
    def get_entities_as_of(as_of):
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