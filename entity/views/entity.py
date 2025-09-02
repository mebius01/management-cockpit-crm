from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.db.models.fields import UUIDField
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from entity.models import Entity
from entity.serializers import EntityListQuerySerializer, EntitySerializer
from entity.serializers.temporal import EntityHistorySerializer
from entity.services import EntityService
from entity.services.history import HistoryService
from services import PaginationService


class EntityViewSet(ModelViewSet):
    """ViewSet for handling entity operations."""

    lookup_field = "entity_uid"
    queryset = Entity.objects.filter(is_current=True)
    serializer_class = EntitySerializer

    def list(self, request: Request) -> Response:
        """Handles GET request to list and filter entities."""
        srz = EntityListQuerySerializer(data=request.query_params)
        srz.is_valid(raise_exception=True)
        query_params = srz.validated_data
        queryset = self._build_filtered_queryset(query_params)

        return PaginationService.paginate_queryset(
            queryset, request, EntitySerializer
        )

    def retrieve(self, _: Request, entity_uid: UUIDField) -> Response:
        """Handles GET request to retrieve a specific entity by UUID."""
        entity = get_object_or_404(
            Entity.objects.select_related("entity_type").prefetch_related("details__detail_type"),
            entity_uid=entity_uid,
            is_current=True
        )
        return Response(EntitySerializer(entity).data)

    def create(self, request: Request) -> Response:
        """Handles POST request to create a new entity."""
        serializer = EntitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Ensure user is of correct type or None
        if not (request.user.is_authenticated and isinstance(request.user, User)):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user: User = request.user

        # Use serializer.save() to trigger the create method and get processed data
        processed_data = serializer.save()
        entity = EntityService().create(processed_data, user)

        return Response(EntitySerializer(entity).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request: Request, entity_uid: UUIDField) -> Response:
        """Handles PATCH request to update a specific entity by UUID."""
        entity = get_object_or_404(
            Entity.objects.select_related("entity_type").prefetch_related("details__detail_type"),
            entity_uid=entity_uid,
            is_current=True
        )

        serializer = EntitySerializer(
            instance=entity,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        if not (request.user.is_authenticated and isinstance(request.user, User)):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user: User = request.user

        entity = EntityService().update(entity_uid, serializer.validated_data, user)

        return Response(EntitySerializer(entity).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request: Request, entity_uid: UUIDField) -> Response:
        """Handles GET request to retrieve combined history for a specific entity."""
        get_object_or_404(
            Entity.objects.filter(entity_uid=entity_uid),
            entity_uid=entity_uid
        )

        history_data = HistoryService.get_combined_history(entity_uid)

        return PaginationService.paginate_queryset(
            history_data, request, EntityHistorySerializer
        )

    def _build_filtered_queryset(self, params: dict) -> QuerySet[Entity]:
        """Build filtered queryset."""
        queryset = Entity.objects.filter(is_current=True).select_related(
            "entity_type"
        ).prefetch_related("details__detail_type")

        if q := params.get("q"):
            queryset = queryset.filter(display_name__icontains=q)
        if entity_type := params.get("type"):
            queryset = queryset.filter(entity_type=entity_type)

        return queryset




    # def partial_update(self, request: Request, entity_uid: UUID) -> Response:
    #     """Handles PATCH request to update a specific entity by UUID."""
    #     entity = get_object_or_404(Entity, entity_uid=entity_uid, is_current=True)
    #     # Validate input (partial update)
    #     serializer = EntityRWSerializer(
    #         instance=entity, data=request.data, partial=True
    #     )
    #     serializer.is_valid(raise_exception=True)

    #     user = request.user if request.user.is_authenticated and isinstance(request.user, User) else None

    #     entity_hashdiff = getattr(entity, "hashdiff", "") or ""


    #     # Update logic for Entity
    #     updated_entity_data = EntityService.update_entity(
    #         str(entity_uid),
    #         serializer.validated_data,
    #         user,
    #         current_entity_hash=entity_hashdiff,
    #     )

    #     # Update logic for EntityDetail
    #     has_details = self._has_details(serializer.validated_data)

    #     # 1. Get details that have is_current=True from the old model
    #     current_details = []
    #     detail_hashdiffs = []
    #     if has_details:
    #         current_details = list(
    #             EntityDetail.objects.filter(entity=entity, is_current=True).select_related('detail_type')
    #         )
    #         # 2. also their hashes
    #         detail_hashdiffs = [detail.hashdiff for detail in current_details]

    #     # 3. separate details from input data
    #     entity_data = {}
    #     details_data = []

    #     for key, value in serializer.validated_data.items():
    #         if key in ['input_details', 'details']:
    #             details_data = value if isinstance(value, list) else []
    #         else:
    #             entity_data[key] = value

    #     # 4. process all of this
    #     # First update Entity if there are changes
    #     if entity_data:
    #         updated_entity_data = EntityService.update_entity(
    #             str(entity_uid),
    #             entity_data,
    #             user,
    #             current_entity_hash=entity_hashdiff,
    #         )


    #     # Return result
    #     if updated_entity_data is None:
    #         # No changes were made
    #         return Response(EntityRWSerializer(entity).data)

    #     # Get the updated entity with details
    #     updated_entity = Entity.objects.get(entity_uid=entity_uid, is_current=True)
    #     return Response(EntityRWSerializer(updated_entity).data)
