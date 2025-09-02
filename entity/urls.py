from django.urls import include, path
from rest_framework.routers import DefaultRouter

from entity.views import EntitiesAsOfAPIView, EntitiesDiffAPIView, EntityViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'entities', EntityViewSet, basename='entity')

urlpatterns = [
    path('', include(router.urls)),
    # Temporal query endpoints
    path('entities-asof/', EntitiesAsOfAPIView.as_view(), name='entities-asof'),
    path('diff/', EntitiesDiffAPIView.as_view(), name='entities-diff'),
]