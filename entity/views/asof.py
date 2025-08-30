from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from entity.services.asof import AsOfService
from entity.serializers import (
    EntitySerializer,
    EntityDetailSerializer,
    AsOfFilterSerializer,
)


class AsOfAPIView(APIView):
    def get(self, request: Request):
        filter_serializer = AsOfFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        
        as_of = filter_serializer.validated_data.get("as_of")
        try:
            queryset = AsOfService.get_queryset({"as_of": as_of})
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        paginator, paginated_queryset = AsOfService.paginate_queryset(queryset, request)

        result = [
            {
                "entity": EntitySerializer(e).data,
                "details": EntityDetailSerializer(e.details_as_of, many=True).data,
            }
            for e in paginated_queryset
        ]
        return paginator.get_paginated_response(result)