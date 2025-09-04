"""
Ping endpoint for application health monitoring
"""
import os
import sys
from datetime import datetime

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def ping(request) -> JsonResponse:
    """
    Comprehensive ping endpoint for health monitoring
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    # Gather application information
    app_info = {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "debug": settings.DEBUG,
            "environment": os.getenv("DJANGO_ENVIRONMENT", "development"),
            "python_version": sys.version.split()[0],
            "django_version": getattr(settings, "DJANGO_VERSION", "unknown"),
        },
        "database": db_status,
        "features": {
            "scd2_versioning": True,
            "temporal_queries": True,
            "audit_logging": True,
            "token_auth": True,
        },
        "endpoints": {
            "api_base": "/api/v1/",
            "admin": "/admin/",
            "ping": "/ping/",
        }
    }
    
    # Return appropriate status code
    status_code = 200 if app_info["status"] == "healthy" else 503
    
    return JsonResponse(app_info, status=status_code)
