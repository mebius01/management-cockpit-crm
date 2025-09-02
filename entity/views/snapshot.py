from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from entity.services.get import GetService
from entity.services.update import UpdateService
from entity.serializers import (
    EntitySerializer,
    EntityDetailSerializer,
    EntityPatchSerializer,
)

class SnapshotAPIView(APIView):
    def get(self, request: Request, entity_uid: str):
        entity = GetService.get_entity(entity_uid)
        if not entity:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "entity": EntitySerializer(entity).data,
            "details": EntityDetailSerializer(entity.details.filter(is_current=True), many=True).data,
        }
        return Response(data)

    def patch(self, request: Request, entity_uid: str):
        serializer = EntityPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        entity = UpdateService.update_entity(
            entity_uid, serializer.validated_data
        )

        if not entity:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "entity": EntitySerializer(entity).data,
            "details": EntityDetailSerializer(
                entity.details.filter(is_current=True), many=True
            ).data,
        }
        return Response(data)
