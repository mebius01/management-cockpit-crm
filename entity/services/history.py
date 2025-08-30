from entity.models import Entity


class HistoryService:
    @staticmethod
    def get_history(entity_uid: str):
        return Entity.objects.filter(entity_uid=entity_uid).order_by("-valid_from")