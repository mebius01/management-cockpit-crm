import uuid
from threading import local

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

# Thread-local storage for request context
_request_context = local()


class AuditContextMiddleware(MiddlewareMixin):
    """
    Middleware to capture request context for audit logging.
    Stores IP address, user agent, user, and request ID in thread-local storage.
    """

    def process_request(self, request):
        """Extract and store request context for audit logging."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Get client IP address
        ip_address = self._get_client_ip(request)

        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Get authenticated user - require authentication for audit operations
        user = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user

        # Store in thread-local storage
        _request_context.request_id = request_id
        _request_context.ip_address = ip_address
        _request_context.user_agent = user_agent
        _request_context.user = user

        # Also store in request for easy access
        request.audit_context = {
            'request_id': request_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'user': user
        }

    def process_response(self, request, response):
        """Clean up thread-local storage after request."""
        self._clear_context()
        return response

    def process_exception(self, request, exception):
        """Clean up thread-local storage on exception."""
        self._clear_context()

    def _get_client_ip(self, request):
        """Extract client IP address from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _clear_context(self):
        """Clear thread-local storage."""
        for attr in ['request_id', 'ip_address', 'user_agent', 'user']:
            if hasattr(_request_context, attr):
                delattr(_request_context, attr)


class AuditContext:
    """
    Utility class to access audit context from anywhere in the application.
    """

    @classmethod
    def get_context(cls) -> dict:
        """Get current request audit context."""
        return {
            'request_id': getattr(_request_context, 'request_id', None),
            'ip_address': getattr(_request_context, 'ip_address', None),
            'user_agent': getattr(_request_context, 'user_agent', None),
            'user': getattr(_request_context, 'user', None)
        }

    @classmethod
    def get_user(cls):
        """Get current authenticated user."""
        return getattr(_request_context, 'user', None)

    @classmethod
    def get_request_id(cls) -> str:
        """Get current request ID."""
        return getattr(_request_context, 'request_id', None)

    @classmethod
    def require_authenticated_user(cls):
        """
        Get authenticated user or raise exception if not authenticated.
        Use this for operations that require audit logging.
        """
        user = cls.get_user()
        if not user:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Authentication required for this operation")
        return user
