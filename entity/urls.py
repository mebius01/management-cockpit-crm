<<<<<<< HEAD
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from entity.views import EntityViewSet, EntitiesAsOfAPIView, EntitiesDiffAPIView

router = DefaultRouter(trailing_slash=False)
router.register(r'entities', EntityViewSet, basename='entity')

urlpatterns = [
    path('', include(router.urls)),
    # Temporal query endpoints
    path('entities-asof/', EntitiesAsOfAPIView.as_view(), name='entities-asof'),
    path('diff/', EntitiesDiffAPIView.as_view(), name='entities-diff'),
=======
from django.urls import path
from entity.views import (
    EntityAPIView,
    SnapshotAPIView,
    HistoryAPIView,
    AsOfAPIView,
    DiffAPIView,
)

urlpatterns = [
    path('entities', EntityAPIView.as_view(), name='entities-list-create'),
    path('entities/<uuid:entity_uid>', SnapshotAPIView.as_view(), name='entity-snapshot'),
    path('entities/<uuid:entity_uid>/history', HistoryAPIView.as_view(), name='entity-history'),
    path('entities-asof', AsOfAPIView.as_view(), name='entities-as-of'),
    path('diff', DiffAPIView.as_view(), name='entities-diff'),
>>>>>>> main
]