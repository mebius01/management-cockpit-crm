from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from services.datetime import DateTimeService
from entity.services import (
    AsOfService, 
    DiffService
    )
from entity.serializers import (
    AsOfQuerySerializer,
    DiffQuerySerializer,
    EntitySnapshotSerializer,
    EntityChangeSerializer
)
from services import PaginationService


class EntitiesAsOfAPIView(APIView):
    """API view for getting entity snapshots at specific point in time."""
    
    def get(self, request: Request):
        """Returns snapshot of all entities as they existed at the specified date."""
        query_serializer = AsOfQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        try:
            as_of_date = DateTimeService.validate_and_parse(query_serializer.validated_data['as_of'])
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        entities_snapshot = AsOfService.get_entities_as_of(as_of_date)
        return PaginationService.paginate_queryset(
            entities_snapshot, request, EntitySnapshotSerializer, many=True
        )


class EntitiesDiffAPIView(APIView):
    """API view for getting entity changes between two dates."""
    
    def get(self, request: Request):
        """Returns list of changes that occurred between the two dates."""
        query_serializer = DiffQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        from_date = query_serializer.validated_data['parsed_from_date']
        to_date = query_serializer.validated_data['parsed_to_date']
        
        changes = DiffService.get_entities_diff(from_date, to_date)
        
        return PaginationService.paginate_queryset(
            changes, request, EntityChangeSerializer, many=True
        )
