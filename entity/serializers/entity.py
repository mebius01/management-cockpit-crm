from rest_framework import serializers
from entity.models import Entity, EntityDetail, EntityType, DetailType

class EntityDetailSerializer(serializers.ModelSerializer):
    detail_type = serializers.CharField(source='detail_type.name', read_only=True)

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

class SEntityListQuery(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, required=False, help_text="Page number for pagination")
    q = serializers.CharField(max_length=255, required=False, help_text="Search query for entity display name")
    type = serializers.SlugRelatedField(
        slug_field="code",
        queryset=EntityType.objects.all(),
        required=False,
        help_text="Filter by entity type code"
    )

class EntityDetailInline(serializers.Serializer):
    detail_type = serializers.SlugRelatedField(slug_field="code", queryset=DetailType.objects.all())
    detail_value = serializers.CharField()
    valid_from = serializers.DateTimeField(required=False)

class EntityRWSerializer(serializers.ModelSerializer):
    # write
    entity_type_code = serializers.SlugRelatedField(
        slug_field="code",
        source="entity_type",
        queryset=EntityType.objects.all(),
        write_only=True,
        required=True,
    )
    input_details = EntityDetailInline(many=True, write_only=True, required=False)

    # read
    entity_type = serializers.CharField(source='entity_type.name', read_only=True)
    details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Entity
        fields = (
            "id",
            "entity_uid",
            "display_name",
            "entity_type_code",   # write
            "entity_type",        # read
            "valid_from",
            "valid_to",
            "is_current",
            "created_at",
            "updated_at",
            "input_details",      # write
            "details",            # read
        )
        read_only_fields = ("id", "entity_uid", "valid_to", "is_current", "created_at", "updated_at")

    def to_internal_value(self, data):
        mutable = dict(data)
        if "entity_type_code" not in mutable and "entity_type" in mutable and isinstance(mutable["entity_type"], str):
            mutable["entity_type_code"] = mutable["entity_type"]
        if "input_details" not in mutable and "details" in mutable and isinstance(mutable["details"], (list, tuple)):
            mutable["input_details"] = mutable["details"]
        return super().to_internal_value(mutable)

    def get_details(self, obj):
        current_details = EntityDetail.objects.filter(entity=obj, is_current=True).select_related('detail_type')
        return EntityDetailSerializer(current_details, many=True).data

    def create(self, validated_data):
        from django.db import transaction
        details_payload = validated_data.pop("input_details", None) or []
        with transaction.atomic():
            entity = Entity.objects.create(**validated_data)
            for det in details_payload:
                det_kwargs = {
                    "entity": entity,
                    "detail_type": det["detail_type"],
                    "detail_value": det["detail_value"],
                }
                if det.get("valid_from") is not None:
                    det_kwargs["valid_from"] = det["valid_from"]
                EntityDetail.objects.create(**det_kwargs)
        return entity

class EntityHistorySerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=['entity', 'detail'])
    valid_from = serializers.DateTimeField()
    valid_to = serializers.DateTimeField(allow_null=True)
    is_current = serializers.BooleanField()
    changes = serializers.DictField()
    hashdiff = serializers.CharField()
    entity_uid = serializers.UUIDField()