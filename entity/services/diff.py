from datetime import datetime
from typing import Dict, Any, Union

from django.db.models import Q

from entity.models import Entity, EntityDetail
from entity.services.datetime_validation import DateTimeValidationService


class DiffService:
    """Service class for handling diff logic."""
    @staticmethod
    def validate_diff_params(fr: Union[str, datetime, None], to: Union[str, datetime, None]) -> tuple[datetime, datetime]:
        """Validate and parse both from and to parameters for diff operations."""
        from_dt = DateTimeValidationService.parse_datetime(fr)
        to_dt = DateTimeValidationService.parse_datetime(to)
        
        if from_dt >= to_dt:
            raise ValueError("'from' datetime must be earlier than 'to' datetime")
        
        return from_dt, to_dt

    @staticmethod
    def get_snapshot(dt: datetime) -> Dict[str, Dict[str, Any]]:
        """Get snapshot of all entities at a specific datetime."""
        # Map entity_uid -> { core fields, details: {code: value} }
        snap: Dict[str, Dict[str, Any]] = {}
        ents = Entity.objects.filter(valid_from__lte=dt).filter(Q(valid_to__gt=dt) | Q(valid_to__isnull=True))
        for e in ents:
            snap[str(e.entity_uid)] = {
                "display_name": e.display_name,
                "entity_type": e.entity_type.code,
                "details": {},
            }
        if not snap:
            return snap
        details = EntityDetail.objects.filter(
            entity__entity_uid__in=snap.keys(),
            valid_from__lte=dt
        ).filter(Q(valid_to__gt=dt) | Q(valid_to__isnull=True))
        for d in details:
            uid = str(d.entity.entity_uid)
            if uid in snap:
                snap[uid]["details"][d.detail_type.code] = d.detail_value
        return snap

    @staticmethod
    def get_entities_diff(fr: Union[str, datetime, None], to: Union[str, datetime, None]) -> list:
        """Get structured diff between two points in time, grouped by entity."""
        from_dt, to_dt = DiffService.validate_diff_params(fr, to)
        before = DiffService.get_snapshot(from_dt)
        after = DiffService.get_snapshot(to_dt)
        uids = sorted(set(before.keys()) | set(after.keys()))
        
        # Group changes by entity
        entities_changes = {}
        
        for uid in uids:
            b = before.get(uid, {})
            a = after.get(uid, {})
            entity_changes = {"entity_uid": uid, "changes": []}
            
            if not b and a:
                entity_changes["changes"].append({"type": "entity", "action": "created"})
                b = {"details": {}}
            elif b and not a:
                entity_changes["changes"].append({"type": "entity", "action": "deleted"})
                a = {"details": {}}
            
            # Core field changes
            core_fields = ["display_name", "entity_type"]
            for field in core_fields:
                if b.get(field) != a.get(field):
                    entity_changes["changes"].append({
                        "type": "field",
                        "field": field,
                        "from": b.get(field),
                        "to": a.get(field),
                    })
            
            # Detail changes
            codes = sorted(set(b.get("details", {}).keys()) | set(a.get("details", {}).keys()))
            for code in codes:
                old_value = b.get("details", {}).get(code)
                new_value = a.get("details", {}).get(code)
                if old_value != new_value:
                    entity_changes["changes"].append({
                        "type": "detail",
                        "field": code,
                        "from": old_value,
                        "to": new_value,
                    })
            
            if entity_changes["changes"]:
                entities_changes[uid] = entity_changes
        
        return list(entities_changes.values())