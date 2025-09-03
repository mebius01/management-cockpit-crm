from datetime import datetime
from typing import Any

from rest_framework import serializers

from services.datetime import DateTimeService


class AsOfQuerySerializer(serializers.Serializer):
    as_of = serializers.CharField(help_text="Date in YYYY-MM-DD format")

    def validate_as_of(self, value: str) -> datetime:
        """Validate and parse the as_of date parameter, returning datetime object."""
        try:
            return DateTimeService.validate_and_parse(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e)) from e

class DiffQuerySerializer(serializers.Serializer):
    from_date = serializers.CharField(help_text="Start date in YYYY-MM-DD format")
    to_date = serializers.CharField(help_text="End date in YYYY-MM-DD format")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if 'data' in kwargs and kwargs['data']:
            data = kwargs['data'].copy()
            if 'from' in data:
                data['from_date'] = data['from']
            if 'to' in data:
                data['to_date'] = data['to']
            kwargs['data'] = data
        super().__init__(*args, **kwargs)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        try:
            from_date = DateTimeService.validate_and_parse(attrs['from_date'])
            to_date = DateTimeService.validate_and_parse(attrs['to_date'])
        except ValueError as e:
            raise serializers.ValidationError(str(e)) from e

        if from_date >= to_date:
            error_msg = 'from_date must be earlier than to_date'
            raise serializers.ValidationError(error_msg)

        attrs['parsed_from_date'] = from_date
        attrs['parsed_to_date'] = to_date
        return attrs

class EntitySnapshotSerializer(serializers.Serializer):
    entity_uid = serializers.UUIDField()
    display_name = serializers.CharField()
    entity_type = serializers.CharField(allow_null=True)
    valid_from = serializers.DateTimeField()
    valid_to = serializers.DateTimeField(allow_null=True)
    hashdiff = serializers.CharField()
    details = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=True
    )

class EntityDiffResponseSerializer(serializers.Serializer):
    """Serializer for the diff endpoint response format."""
    entity_uid = serializers.UUIDField()
    changes = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=True
    )


class EntityHistorySerializer(serializers.Serializer):
    """Serializer for entity history entries."""
    type = serializers.ChoiceField(choices=['entity', 'detail'])
    valid_from = serializers.DateTimeField()
    valid_to = serializers.DateTimeField(allow_null=True)
    is_current = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    hashdiff = serializers.CharField()
    entity_uid = serializers.UUIDField()
    changes = serializers.DictField()

