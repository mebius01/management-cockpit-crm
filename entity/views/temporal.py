from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from entity.serializers import (
    AsOfQuerySerializer,
    DiffQuerySerializer,
    EntityDiffResponseSerializer,
    EntitySerializer,
)
from entity.services import AsOfService, DiffService
from services import PaginationService


class AsOfAPIView(APIView):
    """API view for getting entity snapshots at specific point in time."""

    def get(self, request: Request) -> Response:
        """Returns snapshot of all entities as they existed at the specified date."""
        query_serializer = AsOfQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        as_of_date = query_serializer.validated_data['as_of']
        entities_queryset = AsOfService.get_entities_as_of(as_of_date)
        return PaginationService.paginate_queryset(
            entities_queryset, request, EntitySerializer, many=True
        )


class DiffAPIView(APIView):
    """API view for getting entity changes between two dates."""

    def get(self, request: Request) -> Response:
        """Returns list of changes that occurred between the two dates."""
        query_serializer = DiffQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        from_date = query_serializer.validated_data['parsed_from_date']
        to_date = query_serializer.validated_data['parsed_to_date']

        changes = DiffService.get_entities_diff(from_date, to_date)

        return PaginationService.paginate_queryset(
            changes, request, EntityDiffResponseSerializer, many=True
        )
