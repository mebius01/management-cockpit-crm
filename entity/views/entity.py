from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ViewSet
from django.db import transaction

from entity.serializers import SEntityListQuery, EntityRWSerializer
from entity.models import Entity
from services import PaginationService

class EntityViewSet(ViewSet):
    """ViewSet for handling entity operations."""

    def list(self, request: Request):
        """Handles GET request to list and filter entities."""

        request_serializer = SEntityListQuery(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)
        query_params = request_serializer.validated_data

        queryset = self._build_filtered_queryset(query_params)

        return PaginationService.paginate_queryset(queryset, request, EntityRWSerializer)

    @transaction.atomic
    def create(self, request: Request):
        """Handles POST request to create a new entity."""
        serializer = EntityRWSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        entity = serializer.save()
        return Response(EntityRWSerializer(entity).data, status=status.HTTP_201_CREATED)

    def _build_filtered_queryset(self, query_params: dict):
        """Build queryset with applied filters based on validated parameters."""
        queryset = Entity.objects.filter(is_current=True).select_related('entity_type')
        
        if 'q' in query_params:
            queryset = queryset.filter(
                display_name__icontains=query_params['q']
            )
        
        if 'type' in query_params:
            queryset = queryset.filter(entity_type=query_params['type'])
        
        return queryset