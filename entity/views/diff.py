from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from entity.services.diff import DiffService
from entity.serializers import DiffFilterSerializer


class DiffAPIView(APIView):
    def get(self, request: Request):
        filter_serializer = DiffFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        
        fr = filter_serializer.validated_data.get("from")
        to = filter_serializer.validated_data.get("to")
        
        changes = DiffService.get_entities_diff(fr, to)
        return Response(changes)
