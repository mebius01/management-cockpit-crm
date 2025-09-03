from typing import Any

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.fields import UUIDField
from django.utils import timezone

from entity.models import DetailType, Entity, EntityDetail
from services.audit import AuditService
from services.hash import HashService
from services.scd2 import SCD2Service


class EntityService:
    """
    Service for creating and updating Entity and EntityDetail in SCD Type 2 style.

    Scenarios handled:
    1. Create Entity without details
    2. Create Entity with details
    3. Update Entity only (no details in input)
    4. Update Entity with unchanged details
    5. Update Entity with changed/new details
    """

    @staticmethod
    def _parse_input_data(data: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
        """Parses input data into Entity data and details list."""
        entity_data = {
            "display_name": data.get("display_name"),
            "entity_type": data.get("entity_type")
        }
        details_data = data.get("details", [])
        if not entity_data["display_name"] or not entity_data["entity_type"]:
            msg = "display_name and entity_type are required"
            raise ValidationError(msg)
        return entity_data, details_data

    @staticmethod
    def _get_detail_type(detail_type_code: str) -> DetailType:
        """Get DetailType by code or raise validation error."""
        try:
            return DetailType.objects.get(code=detail_type_code)
        except DetailType.DoesNotExist as err:
            msg = f"DetailType with code '{detail_type_code}' not found"
            raise ValidationError(msg) from err

    @staticmethod
    def _create_detail_instance(
        entity: Entity,
        detail_type: DetailType,
        detail_value: str,
        user: User
    ) -> EntityDetail:
        """Creates EntityDetail instance with common parameters."""
        entity_detail = EntityDetail(
            entity=entity,
            detail_type=detail_type,
            detail_value=detail_value,
            valid_from=entity.valid_from,
            valid_to=None,
            is_current=True,
        )
        AuditService.log_detail_change(
            entity_uid=entity.entity_uid,
            operation="INSERT",
            user=user,
            before_data={},
            after_data={
                "detail_value": detail_value,
                "detail_type": detail_type.code,
            },
            request_context={}
        )
        entity_detail.save()
        return entity_detail

    @staticmethod
    def _is_detail_unchanged(old_detail: EntityDetail, detail_type: DetailType, detail_value: str) -> bool:
        """Check if detail has changed by comparing hash."""
        new_hashdiff = HashService.compute([detail_value, str(detail_type.code)])
        return new_hashdiff == old_detail.hashdiff

    @transaction.atomic
    def create(self, data: dict[str, Any], user: User) -> Entity:
        """Creates Entity with/without details, handling scenarios 1 & 2."""
        entity_data, details_data = self._parse_input_data(data)
        entity_type = entity_data["entity_type"]
        entity = Entity(
            display_name=entity_data["display_name"],
            entity_type=entity_type,
            valid_from=timezone.now(),
            valid_to=None,
            is_current=True,
        )
        entity.save()
        # Create audit log
        AuditService.log_entity_change(
            entity_uid=entity.entity_uid,
            operation="INSERT",
            user=user,
            before_data={},
            after_data={
                "display_name": entity.display_name,
                "entity_type": entity.entity_type.code,
            },
            request_context={}
        )

        if details_data:
            for detail in details_data:
                detail_type = self._get_detail_type(detail["detail_type"])
                # Create detail and save instance and log audit
                self._create_detail_instance(
                    entity,
                    detail_type,
                    detail["detail_value"],
                    user)

        return entity

    @transaction.atomic
    def update(self, entity_uid: UUIDField, data: dict[str, Any], user: User) -> Entity:
        """Updates Entity with/without details, handling scenarios 3, 4 & 5."""
        entity_data, details_data = self._parse_input_data(data)
        current_entity = self._get_current_entity(entity_uid)

        if self._is_entity_unchanged(current_entity, entity_data, details_data):
            return current_entity

        new_entity = self._create_new_entity_version(current_entity, entity_data)
        self._synchronize_details(current_entity, new_entity, details_data, user)

        return new_entity

    def _get_current_entity(self, entity_uid: UUIDField) -> Entity:
        """Get current entity or raise validation error."""
        try:
            return Entity.objects.get(entity_uid=entity_uid, is_current=True)
        except Entity.DoesNotExist as err:
            msg = f"Entity with entity_uid {entity_uid} not found"
            raise ValidationError(msg) from err

    def _is_entity_unchanged(self, current_entity: Entity, entity_data: dict[str, Any], details_data: list) -> bool:
        entity_type = entity_data["entity_type"]
        new_hashdiff = HashService.compute(
            [str(entity_data["display_name"]), str(entity_type.code)]
        )
        entity_unchanged = new_hashdiff == current_entity.hashdiff

        if not details_data:
            return entity_unchanged

        details_unchanged = self._are_details_unchanged(current_entity, details_data)
        return entity_unchanged and details_unchanged

    def _are_details_unchanged(self, current_entity: Entity, details_data: list) -> bool:
        current_details = {d.detail_type.code: d for d in current_entity.details.filter(is_current=True)}

        if len(details_data) != len(current_details):
            return False

        for detail in details_data:
            detail_type_code = detail["detail_type"]
            new_detail_value = detail["detail_value"]

            if detail_type_code not in current_details:
                return False

            current_detail = current_details[detail_type_code]
            detail_type = self._get_detail_type(detail_type_code)

            if not self._is_detail_unchanged(current_detail, detail_type, new_detail_value):
                return False

        return True

    def _create_new_entity_version(self, current_entity: Entity, entity_data: dict[str, Any]) -> Entity:
        entity_type = entity_data["entity_type"]
        old_entity, new_entity = SCD2Service.create_new_version(
            current_entity,
            display_name=entity_data["display_name"],
            entity_type=entity_type
        )
        old_entity.save()
        new_entity.save()
        return new_entity

    def _synchronize_details(self, current_entity: Entity, new_entity: Entity, details_data: list, user: User) -> None:
        current_details = {d.detail_type.code: d for d in current_entity.details.filter(is_current=True)}

        if details_data:
            self._process_provided_details(new_entity, current_details, details_data, user)
            self._close_unprovided_details(new_entity, current_details, details_data)
        else:
            self._copy_existing_details(new_entity, current_details)

    def _process_provided_details(
        self, new_entity: Entity, current_details: dict, details_data: list, user: User
    ) -> None:
        for detail in details_data:
            detail_type = self._get_detail_type(detail["detail_type"])
            new_detail_value = detail["detail_value"]
            old_detail = current_details.get(detail_type.code)

            if old_detail:
                self._update_existing_detail(old_detail, new_entity, detail_type, new_detail_value, user)
            else:
                self._create_new_detail(new_entity, detail_type, new_detail_value, user)

    def _update_existing_detail(self, old_detail: EntityDetail, new_entity: Entity,
                                detail_type: DetailType, new_detail_value: str, user: User) -> None:
        if self._is_detail_unchanged(old_detail, detail_type, new_detail_value):
            # Scenario 4: Detail unchanged, just copy with new entity reference
            new_detail = self._create_detail_instance(new_entity, detail_type, new_detail_value, user)
            new_detail.save()
        else:
            # Scenario 5: Detail changed, use SCD2 to close old and create new
            old_detail, new_detail = SCD2Service.create_new_version(
                old_detail,
                entity=new_entity,
                detail_type=detail_type,
                detail_value=new_detail_value
            )
            old_detail.save()
            new_detail.save()

    def _create_new_detail(self, new_entity: Entity, detail_type: DetailType, detail_value: str, user: User) -> None:
        new_detail = self._create_detail_instance(new_entity, detail_type, detail_value, user)
        new_detail.save()

    def _close_unprovided_details(self, new_entity: Entity, current_details: dict, details_data: list) -> None:
        provided_detail_types = {d["detail_type"] for d in details_data}

        for detail_type_code, old_detail in current_details.items():
            if detail_type_code not in provided_detail_types:
                old_detail, new_detail = SCD2Service.create_new_version(
                    old_detail,
                    entity=new_entity,
                    detail_type=old_detail.detail_type,
                    detail_value=old_detail.detail_value
                )
                old_detail.save()
                new_detail.save()

    def _copy_existing_details(self, new_entity: Entity, current_details: dict) -> None:
        for old_detail in current_details.values():
            old_detail, new_detail = SCD2Service.create_new_version(
                old_detail,
                entity=new_entity,
                detail_type=old_detail.detail_type,
                detail_value=old_detail.detail_value
            )
            old_detail.save()
            new_detail.save()
