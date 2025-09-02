from typing import Any

from django.db.models import QuerySet
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer


class PaginationService:
    """Service for handling pagination logic across different views."""

    @staticmethod
    def paginate_queryset(
        queryset: QuerySet | list,
        request: Request,
        serializer_class: type[Serializer],
        many: bool = True
    ) -> Response:
        """Paginate queryset and return serialized response."""
        paginator = PageNumberPagination()
        try:
            page = paginator.paginate_queryset(queryset, request)
        except NotFound:
            return Response({
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            })

        if page is not None:
            serializer = serializer_class(page, many=many)
            return paginator.get_paginated_response(serializer.data)

        serializer = serializer_class(queryset, many=many)
        return Response(serializer.data)

    @staticmethod
    def get_paginated_data(
        queryset: QuerySet | list,
        request: Request,
        serializer_class: type[Serializer],
        many: bool = True
        ) -> tuple[Any | None, Any | None]:
        """Get paginated data without creating Response object."""
        paginator = PageNumberPagination()
        try:
            page = paginator.paginate_queryset(queryset, request)
        except NotFound:
            return [], paginator

        if page is not None:
            serializer = serializer_class(page, many=many)
            return serializer.data, paginator

        return None, None
