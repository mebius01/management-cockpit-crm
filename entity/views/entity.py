<<<<<<< HEAD
from uuid import UUID

from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from entity.models import Entity, EntityDetail
from entity.serializers import (
    EntityHistorySerializer,
    EntityRWSerializer,
    SEntityListQuery,
)
from entity.services import HistoryService
from entity.services.entity import EntityService
from services import PaginationService


class EntityViewSet(ModelViewSet):
    """ViewSet for handling entity operations."""

    lookup_field = "entity_uid"
    queryset = Entity.objects.filter(is_current=True)
    serializer_class = EntityRWSerializer

    def list(self, request: Request):
        """Handles GET request to list and filter entities."""
        request_serializer = SEntityListQuery(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)
        query_params = request_serializer.validated_data
        queryset = self._build_filtered_queryset(query_params)

        return PaginationService.paginate_queryset(
            queryset, request, EntityRWSerializer
        )

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

    def partial_update(self, request: Request, entity_uid: UUID):
        """Handles PATCH request to update a specific entity by UUID."""
        entity = get_object_or_404(Entity, entity_uid=entity_uid, is_current=True)
        # Validate input (partial update)
        serializer = EntityRWSerializer(
            instance=entity, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        user = request.user if request.user.is_authenticated else None

        entity_hashdiff = getattr(entity, "hashdiff", None)


        # Update logic for Entity
        updated_entity_data = EntityService.update_entity(
            str(entity_uid),
            serializer.validated_data,
            user,
            current_entity_hash=entity_hashdiff,
        )

        # Update logic for EntityDetail
        has_details = self._has_details(serializer.validated_data)
        
        # 1. Get details that have is_current=True from the old model
        current_details = []
        detail_hashdiffs = []
        if has_details:
            current_details = list(
                EntityDetail.objects.filter(entity=entity, is_current=True).select_related('detail_type')
            )
            # 2. also their hashes
            detail_hashdiffs = [detail.hashdiff for detail in current_details]

        # 3. separate details from input data
        entity_data = {}
        details_data = []
        
        for key, value in serializer.validated_data.items():
            if key in ['input_details', 'details']:
                details_data = value if isinstance(value, list) else []
            else:
                entity_data[key] = value

        # 4. process all of this
        # First update Entity if there are changes
        if entity_data:
            updated_entity_data = EntityService.update_entity(
                str(entity_uid),
                entity_data,
                user,
                current_entity_hash=entity_hashdiff,
            )


        # Return result
        if updated_entity_data is None:
            # No changes were made
            return Response(EntityRWSerializer(entity).data)

        # Get the updated entity with details
        updated_entity = Entity.objects.get(entity_uid=entity_uid, is_current=True)
        return Response(EntityRWSerializer(updated_entity).data)

    def _has_details(self, validated_data: dict) -> bool:
        """Private helper: returns True if validated_data includes non-empty details payload.

        Note: `EntityRWSerializer.to_internal_value()` normalizes incoming `details` -> `input_details`.
        """
        details = validated_data.get("input_details") or []
        return isinstance(details, (list, tuple)) and len(details) > 0

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request: Request, entity_uid: UUID):
        """Handles GET request to retrieve combined history for a specific entity."""
        # Check if any entity with this entity_uid exists
        if not Entity.objects.filter(entity_uid=entity_uid).exists():
            raise Http404("Entity not found")
        
        history_data = HistoryService.get_combined_history(str(entity_uid))
        serializer = EntityHistorySerializer(history_data, many=True)

        return Response(serializer.data)

    def _build_filtered_queryset(self, query_params: dict):
        """Build queryset with applied filters based on validated parameters."""
        queryset = Entity.objects.filter(is_current=True).select_related("entity_type")

        if "q" in query_params:
            queryset = queryset.filter(display_name__icontains=query_params["q"])

        if "type" in query_params:
            queryset = queryset.filter(entity_type=query_params["type"])

        return queryset
=======
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from entity.serializers import EntitySerializer, EntityCreateSerializer, EntityFilterSerializer
from entity.services import ListService, CreateService

class EntityAPIView(APIView):
    """Handles both listing (GET) and creation (POST) of entities."""

    def get(self, request: Request):
        """Handles GET request to list and filter entities."""
        filter_serializer = EntityFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        qs = ListService.get_queryset(filter_serializer.validated_data)
        page, paginator = ListService.paginate_queryset(qs, request)
        
        serializer = EntitySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request: Request):
        """Handles POST request to create a new entity."""
        serializer = EntityCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        snapshot = CreateService.create_entity(serializer.validated_data)
        return Response(snapshot, status=status.HTTP_201_CREATED)

>>>>>>> main
