from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from django.db import transaction
from django.shortcuts import get_object_or_404
from uuid import UUID

from entity.serializers import (
    SEntityListQuery,
    EntityRWSerializer,
    EntityHistorySerializer,
)
from entity.models import Entity
from services import PaginationService
from entity.services import HistoryService
from entity.services.entity import EntityService

class EntityViewSet(ModelViewSet):
    """ViewSet for handling entity operations."""
    lookup_field = 'entity_uid'
    queryset = Entity.objects.filter(is_current=True)
    serializer_class = EntityRWSerializer

    def list(self, request: Request):
        """Handles GET request to list and filter entities."""
        request_serializer = SEntityListQuery(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)
        query_params = request_serializer.validated_data
        queryset = self._build_filtered_queryset(query_params)

        return PaginationService.paginate_queryset(queryset, request, EntityRWSerializer)

    def retrieve(self, request: Request, entity_uid: UUID):
        """Handles GET request to retrieve a specific entity by UUID."""
        entity = get_object_or_404(Entity, entity_uid=entity_uid, is_current=True)
        return Response(EntityRWSerializer(entity).data)

    def create(self, request: Request):
        """Handles POST request to create a new entity."""
        serializer = EntityRWSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user if request.user.is_authenticated else None
        entity = EntityService.create_entity(serializer.validated_data, user)

        return Response(EntityRWSerializer(entity).data, status=status.HTTP_201_CREATED)

    def patch(self, request: Request, entity_uid: UUID):
        """Handles PATCH request to update a specific entity by UUID."""
        entity = get_object_or_404(Entity, entity_uid=entity_uid, is_current=True)

        serializer = EntityRWSerializer(entity, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        user = request.user if request.user.is_authenticated else None
        updated_entity = EntityService.update_entity(entity_uid, serializer.validated_data, user)
        
        return Response(EntityRWSerializer(updated_entity).data)

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request: Request, entity_uid: UUID):
        """Handles GET request to retrieve combined history for a specific entity."""
        get_object_or_404(Entity, entity_uid=entity_uid)
        history_data = HistoryService.get_combined_history(str(entity_uid))
        serializer = EntityHistorySerializer(history_data, many=True)

        return Response(serializer.data)

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