from typing import Any

from rest_framework import serializers

from entity.models import DetailType, Entity, EntityDetail, EntityType


class EntityDetailSerializer(serializers.ModelSerializer):
    detail_type = serializers.SlugRelatedField(
        slug_field="code",
        queryset=DetailType.objects.filter(is_active=True),
        help_text="Detail type code (e.g., ADDRESS, WEBSITE)"
    )

    class Meta:
        model = EntityDetail
        fields = [
            "detail_type",
            "detail_value",
            "valid_from",
            "valid_to",
            "is_current",
            "hashdiff",
        ]
        read_only_fields = [
            "valid_from",
            "valid_to",
            "is_current",
            "hashdiff",
        ]

    def validate_detail_type(self, value: DetailType)-> DetailType:
        if not value.is_active:
            msg = f"Detail type '{value.code}' is not active"
            raise serializers.ValidationError(msg)
        return value

class EntitySerializer(serializers.ModelSerializer):
    entity_type = serializers.SlugRelatedField(
        slug_field="code",
        queryset=EntityType.objects.filter(is_active=True),
        help_text="Entity type code (e.g., INSTITUTION, PERSON)"
    )
    details = EntityDetailSerializer(many=True, required=False, allow_empty=True, write_only=True)
    entity_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Entity
        fields = [
            "id",
            "entity_uid",
            "display_name",
            "entity_type",
            "details",
            "entity_details",
            "valid_from",
            "valid_to",
            "is_current",
            "hashdiff"
        ]

        read_only_fields = [
            "id",
            "entity_uid",
            "valid_from",
            "valid_to",
            "is_current",
            "hashdiff"
        ]

    def create(self, validated_data: dict) -> dict:
        """Create entity with details, converting DetailType objects to codes."""
        details_data = validated_data.pop('details', [])

        # Convert DetailType objects to codes for service
        if details_data:
            for detail in details_data:
                if hasattr(detail['detail_type'], 'code'):
                    detail['detail_type'] = detail['detail_type'].code

        # Add details back to validated_data
        validated_data['details'] = details_data

        return validated_data

    def get_entity_details(self, obj: Entity) -> Any:
        """Get current entity details for read-only field."""
        current_details = obj.details.filter(is_current=True).select_related('detail_type')
        return EntityDetailSerializer(current_details, many=True).data
