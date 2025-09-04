import zoneinfo
from datetime import datetime
from typing import Union

from django.utils import timezone
from django.utils.dateparse import parse_datetime

class DateTimeService:
    @staticmethod
    def validate_and_parse(param: Union[str, datetime]) -> datetime:
        """Parse and validate datetime parameter format only."""
        if isinstance(param, datetime):
            # Ensure timezone awareness
            if param.tzinfo is None:
                param = timezone.make_aware(param, zoneinfo.ZoneInfo('UTC'))
            return param.astimezone(zoneinfo.ZoneInfo('UTC'))

        if not isinstance(param, str):
            raise ValueError(f"Parameter must be a string or datetime, got {type(param).__name__}")

        dt = parse_datetime(param)
        if dt is None:
            raise ValueError(
                f"Invalid datetime format: '{param}'. "
                "Use ISO 8601 format, e.g., '2024-05-01' or '2024-05-01T12:00:00Z'"
            )

        if dt.tzinfo is None:
            dt = timezone.make_aware(dt, zoneinfo.ZoneInfo('UTC'))

        return dt.astimezone(zoneinfo.ZoneInfo('UTC'))