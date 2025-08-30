from django.urls import path, include
from rest_framework.routers import DefaultRouter
from entity.views import EntityViewSet

router = DefaultRouter()
router.register(r'entities', EntityViewSet, basename='entity')

urlpatterns = [
    path('', include(router.urls)),
    # path('entities/<uuid:entity_uid>', SnapshotAPIView.as_view(), name='entity-snapshot'),
    # path('entities/<uuid:entity_uid>/history', HistoryAPIView.as_view(), name='entity-history'),
    # path('entities-asof', AsOfAPIView.as_view(), name='entities-as-of'),
    # path('diff', DiffAPIView.as_view(), name='entities-diff'),
]