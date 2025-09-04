from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
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
        """
        Handles PATCH request to update a specific entity by UUID.

        Updates entity and/or its details using SCD Type 2 semantics.
        Creates new versions instead of modifying existing records.
        Returns 200 OK with updated entity data.
        """
        try:
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

            # Use serializer.save() to trigger conversion of DetailType objects to codes
            processed_data = serializer.save()
            updated_entity = EntityService().update(entity_uid, processed_data, user)

            return Response(EntitySerializer(updated_entity).data, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request: Request, entity_uid: UUIDField) -> Response:
        """Handles GET request to retrieve combined history for a specific entity."""
        # Check if entity exists (any version)
        if not Entity.objects.filter(entity_uid=entity_uid).exists():
            return Response(
                {"error": f"Entity with UUID {entity_uid} not found"},
                status=status.HTTP_404_NOT_FOUND
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

