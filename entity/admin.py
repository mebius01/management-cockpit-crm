from django.contrib import admin
from .models import EntityType, DetailType, Entity, EntityDetail

@admin.register(EntityType)
class EntityTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(DetailType)
class DetailTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


class EntityDetailInline(admin.TabularInline):
    model = EntityDetail
    extra = 0
    fields = ("detail_type", "detail_value", "valid_from", "valid_to", "is_current")
    readonly_fields = ()  # hashdiff is non-editable on the model, so it's excluded automatically
    show_change_link = True


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "entity_type",
        "entity_uid",
        "valid_from",
        "valid_to",
        "is_current",
        "created_at",
    )
    list_filter = ("entity_type", "is_current")
    search_fields = ("display_name", "entity_uid")
    date_hierarchy = "valid_from"
    inlines = [EntityDetailInline]


@admin.register(EntityDetail)
class EntityDetailAdmin(admin.ModelAdmin):
    def short_value(self, obj):
        v = obj.detail_value or ""
        return (v[:50] + "…") if len(v) > 50 else v
    short_value.short_description = "Value"

    list_display = (
        "entity",
        "detail_type",
        "short_value",
        "valid_from",
        "valid_to",
        "is_current",
        "created_at",
    )
    list_filter = ("detail_type", "is_current")
    search_fields = ("entity__display_name", "detail_value")
    date_hierarchy = "valid_from"
