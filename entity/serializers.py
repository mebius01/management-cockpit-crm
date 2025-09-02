from rest_framework import serializers
from .models import Entity, EntityDetail, EntityType, DetailType


class EntityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityType
        fields = ("code", "name")


class DetailTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetailType
        fields = ("code", "name")


class EntityDetailSerializer(serializers.ModelSerializer):
    detail_type = serializers.SlugRelatedField(slug_field="code", queryset=DetailType.objects.all())

    class Meta:
        model = EntityDetail
        fields = (
            "id",
            "detail_type",
            "detail_value",
            "valid_from",
            "valid_to",
            "is_current",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "valid_to", "is_current")


class EntityCreateDetailInput(serializers.Serializer):
    detail_type = serializers.SlugRelatedField(slug_field="code", queryset=DetailType.objects.all())
    detail_value = serializers.CharField()
    valid_from = serializers.DateTimeField(required=False)


class EntitySerializer(serializers.ModelSerializer):
    entity_type = serializers.SlugRelatedField(slug_field="code", queryset=EntityType.objects.all())

    class Meta:
        model = Entity
        fields = (
            "id",
            "entity_uid",
            "display_name",
            "entity_type",
            "valid_from",
            "valid_to",
            "is_current",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "entity_uid", "valid_to", "is_current", "created_at", "updated_at")


class EntityCreateSerializer(serializers.Serializer):
    display_name = serializers.CharField()
    entity_type = serializers.SlugRelatedField(slug_field="code", queryset=EntityType.objects.all())
    valid_from = serializers.DateTimeField(required=False)
    details = EntityCreateDetailInput(many=True, required=False)


class EntitySnapshotSerializer(serializers.Serializer):
    entity = EntitySerializer()
    details = EntityDetailSerializer(many=True)


class EntityPatchDetailInput(serializers.Serializer):
    detail_type = serializers.SlugRelatedField(slug_field="code", queryset=DetailType.objects.all())
    detail_value = serializers.CharField()


class EntityPatchSerializer(serializers.Serializer):
    display_name = serializers.CharField(required=False)
    entity_type = serializers.SlugRelatedField(slug_field="code", queryset=EntityType.objects.all(), required=False)
    valid_from = serializers.DateTimeField(required=False)
    details = EntityPatchDetailInput(many=True, required=False)


class EntityVersionSerializer(serializers.ModelSerializer):
    entity_type = serializers.SlugRelatedField(slug_field="code", read_only=True)

    class Meta:
        model = Entity
        fields = (
            "id",
            "entity_uid",
            "display_name",
            "entity_type",
            "valid_from",
            "valid_to",
            "is_current",
            "created_at",
            "updated_at",
        )


class EntityFilterSerializer(serializers.Serializer):
    """Validates query parameters for entity filtering."""
    q = serializers.CharField(required=False, max_length=255, help_text="Search term for display name")
    type = serializers.CharField(required=False, help_text="Entity type code (PERSON, INSTITUTION)")
    
    def validate_type(self, value):
        if value and not EntityType.objects.filter(code=value, is_active=True).exists():
            raise serializers.ValidationError(f"Invalid entity type: {value}")
        return value


class EntityHistorySerializer(serializers.Serializer):
    entity_versions = EntityVersionSerializer(many=True)
    detail_versions = EntityDetailSerializer(many=True)


class AsOfFilterSerializer(serializers.Serializer):
    """Validates query parameters for as-of filtering."""
    as_of = serializers.CharField(required=False, help_text="Date/time for as-of query (ISO 8601 format)")
    
    def validate_as_of(self, value):
        if value:
            from entity.services.datetime_validation import DateTimeValidationService
            try:
                return DateTimeValidationService.parse_datetime(value)
            except ValueError as e:
                raise serializers.ValidationError(str(e))
        return None


class DiffFilterSerializer(serializers.Serializer):
    """Validates query parameters for diff filtering."""
    
    def to_internal_value(self, data):
        from_param = data.get('from')
        to_param = data.get('to')
        
        if not from_param:
            raise serializers.ValidationError({'from': ['This field is required.']})
        if not to_param:
            raise serializers.ValidationError({'to': ['This field is required.']})
        
        from entity.services.datetime_validation import DateTimeValidationService
        try:
            from_date = DateTimeValidationService.parse_datetime(from_param)
        except ValueError as e:
            raise serializers.ValidationError({'from': [str(e)]})
        
        try:
            to_date = DateTimeValidationService.parse_datetime(to_param)
        except ValueError as e:
            raise serializers.ValidationError({'to': [str(e)]})
        
        return {
            'from': from_date,
            'to': to_date
        }
