from rest_framework import serializers
from .models import Entity, EntityDetail, EntityType, DetailType


# ============================================================================
# Base Model Serializers
# ============================================================================

class EntityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityType
        fields = ("code", "name")


class DetailTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetailType
        fields = ("code", "name")


class EntitySerializer(serializers.ModelSerializer):
    """Basic Entity serializer without nested relationships."""
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


class EntityDetailSerializer(serializers.ModelSerializer):
    """EntityDetail serializer with nested detail_type."""
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


# ============================================================================
# EntityList
# ============================================================================

class SEntityListQuery(serializers.Serializer):
    """Serializer for validating GET request query parameters for entity listing."""
    page = serializers.IntegerField(min_value=1, required=False, help_text="Page number for pagination")
    q = serializers.CharField(max_length=255, required=False, help_text="Search query for entity display name")
    type = serializers.SlugRelatedField(
        slug_field="code", 
        queryset=EntityType.objects.all(), 
        required=False,
        help_text="Filter by entity type code"
    )


class SEntityWithDetails(serializers.ModelSerializer):
    """Entity serializer with nested entity_type and related details for API responses."""
    entity_type = serializers.CharField(source='entity_type.name', read_only=True)
    details = serializers.SerializerMethodField()

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
            "details",
        )

    def get_details(self, obj):
        """Get current EntityDetails for this entity."""
        current_details = EntityDetail.objects.filter(
            entity=obj,
            is_current=True
        ).select_related('detail_type')
        return EntityDetailSerializer(current_details, many=True).data


# ============================================================================
# EntityCreate
# ============================================================================

class SEntityDetailCreate(serializers.Serializer):
    """Serializer for an individual detail in the create payload."""
    detail_type = serializers.SlugRelatedField(
        slug_field="code",
        queryset=DetailType.objects.all(),
        help_text="Detail type code",
    )
    detail_value = serializers.CharField()
    valid_from = serializers.DateTimeField(required=False)


class SEntityCreate(serializers.Serializer):
    """Serializer for validating POST body to create an Entity.

    Accepts entity_type by its code (slug).
    """
    display_name = serializers.CharField(max_length=255)
    entity_type = serializers.SlugRelatedField(
        slug_field="code",
        queryset=EntityType.objects.all(),
        help_text="Entity type code",
    )
    valid_from = serializers.DateTimeField(required=False)
    details = SEntityDetailCreate(many=True, required=False)


# ============================================================================
# Unified read-write serializer (reduces separate create/read serializers)
# ============================================================================

class EntityDetailInline(serializers.Serializer):
    """Write-only inline detail for creation/update."""
    detail_type = serializers.SlugRelatedField(slug_field="code", queryset=DetailType.objects.all())
    detail_value = serializers.CharField()
    valid_from = serializers.DateTimeField(required=False)


class EntityRWSerializer(serializers.ModelSerializer):
    """Single serializer for both read and write:
    - Write: accepts entity_type_code and details (inline)
    - Read: exposes entity_type name and current details
    """
    # Write inputs
    entity_type_code = serializers.SlugRelatedField(
        slug_field="code",
        source="entity_type",
        queryset=EntityType.objects.all(),
        write_only=True,
        required=True,
    )
    input_details = EntityDetailInline(many=True, write_only=True, required=False)

    # Read outputs
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
        """Backwards compatibility shim:
        - Accept incoming payloads with 'entity_type' (code) instead of 'entity_type_code'.
        - Accept 'details' instead of 'input_details'.
        """
        mutable = dict(data)
        # If client sends entity_type code as 'entity_type', map it
        if "entity_type_code" not in mutable and "entity_type" in mutable and isinstance(mutable["entity_type"], str):
            mutable["entity_type_code"] = mutable["entity_type"]
        # If client sends details list under 'details', map it
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
