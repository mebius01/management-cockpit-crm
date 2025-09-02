from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from typing import Optional, Any
from django.db.models import QuerySet


class PaginationService:
    """Service for handling pagination logic across different views."""
    
    @staticmethod
    def paginate_queryset(queryset: QuerySet, request, serializer_class, many: bool = True) -> Response:
        """
        Paginate a queryset and return serialized response.
        
        Args:
            queryset: Django QuerySet to paginate
            request: DRF Request object
            serializer_class: Serializer class to use for response
            many: Whether to serialize multiple objects
            
        Returns:
            Response: Paginated response or regular response if pagination not applied
        """
        paginator = PageNumberPagination()
        try:
            page = paginator.paginate_queryset(queryset, request)
        except NotFound:
            # Requested page is out of range. Return empty paginated payload instead of 404.
            return Response({
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            })
        
        if page is not None:
            # Paginated response
            serializer = serializer_class(page, many=many)
            return paginator.get_paginated_response(serializer.data)
        
        # Fallback if pagination is not applied
        serializer = serializer_class(queryset, many=many)
        return Response(serializer.data)
    
    @staticmethod
    def get_paginated_data(queryset: QuerySet, request, serializer_class, many: bool = True) -> tuple[Optional[list], Optional[Any]]:
        """
        Get paginated data without creating Response object.
        
        Args:
            queryset: Django QuerySet to paginate
            request: DRF Request object
            serializer_class: Serializer class to use
            many: Whether to serialize multiple objects
            
        Returns:
            tuple: (paginated_data, paginator) or (None, None) if no pagination
        """
        paginator = PageNumberPagination()
        try:
            page = paginator.paginate_queryset(queryset, request)
        except NotFound:
            return [], paginator
        
        if page is not None:
            serializer = serializer_class(page, many=many)
            return serializer.data, paginator
        
        return None, None
