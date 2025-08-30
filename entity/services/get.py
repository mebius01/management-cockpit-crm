from entity.models import Entity
from django.db.models import Q


class GetService:
    @staticmethod
    def get_entity(entity_uid: str):
        try:
            return Entity.objects.get(entity_uid=entity_uid, is_current=True)
        except Entity.DoesNotExist:
            return None