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

