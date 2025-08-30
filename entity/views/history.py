from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from entity.serializers import EntitySerializer
from entity.services.history import HistoryService


class HistoryAPIView(APIView):
    def get(self, request: Request, entity_uid: str):
        entity_versions = HistoryService.get_history(entity_uid)
        serializer = EntitySerializer(entity_versions, many=True)
        return Response(serializer.data)