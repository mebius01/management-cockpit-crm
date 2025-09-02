<<<<<<< HEAD
from typing import List, Dict, Any
from datetime import datetime
from django.db.models import Q
from entity.models import Entity, EntityDetail
from .asof import AsOfService


class DiffService:
    """Service for comparing entity states between two points in time."""
    
    @staticmethod
    def get_entities_diff(from_date: datetime, to_date: datetime) -> List[Dict[str, Any]]:
        """
        Get changes in all entities between two dates.
        
        Args:
            from_date: Start date for comparison
            to_date: End date for comparison
            
        Returns:
            List of changes grouped by entity_uid and field
        """
        changes = []
        
        # Get snapshots at both dates
        from_snapshot = {item['entity_uid']: item for item in AsOfService.get_entities_as_of(from_date)}
        to_snapshot = {item['entity_uid']: item for item in AsOfService.get_entities_as_of(to_date)}
        
        # Find all entity_uids that existed in either snapshot
        all_entity_uids = set(from_snapshot.keys()) | set(to_snapshot.keys())
        
        for entity_uid in all_entity_uids:
            entity_changes = DiffService._compare_entity_snapshots(
                entity_uid, 
                from_snapshot.get(entity_uid), 
                to_snapshot.get(entity_uid)
            )
            changes.extend(entity_changes)
        
        return changes
    
    @staticmethod
    def get_entity_diff(entity_uid: str, from_date: datetime, to_date: datetime) -> List[Dict[str, Any]]:
        """
        Get changes for specific entity between two dates.
        
        Args:
            entity_uid: UUID of the entity
            from_date: Start date for comparison
            to_date: End date for comparison
            
        Returns:
            List of changes for this entity
        """
        from_snapshot = AsOfService.get_entity_as_of(entity_uid, from_date)
        to_snapshot = AsOfService.get_entity_as_of(entity_uid, to_date)
        
        return DiffService._compare_entity_snapshots(entity_uid, from_snapshot, to_snapshot)
    
    @staticmethod
    def _compare_entity_snapshots(entity_uid: str, from_entity: Dict, to_entity: Dict) -> List[Dict[str, Any]]:
        """Compare two entity snapshots and return list of changes."""
        changes = []
        
        # Handle entity creation/deletion
        if from_entity is None and to_entity is not None:
            changes.append({
                'entity_uid': entity_uid,
                'change_type': 'entity_created',
                'field': 'entity',
                'from_value': None,
                'to_value': {
                    'display_name': to_entity['display_name'],
                    'entity_type': to_entity['entity_type']
                }
            })
        elif from_entity is not None and to_entity is None:
            changes.append({
                'entity_uid': entity_uid,
                'change_type': 'entity_deleted',
                'field': 'entity',
                'from_value': {
                    'display_name': from_entity['display_name'],
                    'entity_type': from_entity['entity_type']
                },
                'to_value': None
            })
        elif from_entity is not None and to_entity is not None:
            # Compare entity fields
            if from_entity['display_name'] != to_entity['display_name']:
                changes.append({
                    'entity_uid': entity_uid,
                    'change_type': 'field_changed',
                    'field': 'display_name',
                    'from_value': from_entity['display_name'],
                    'to_value': to_entity['display_name']
                })
            
            if from_entity['entity_type'] != to_entity['entity_type']:
                changes.append({
                    'entity_uid': entity_uid,
                    'change_type': 'field_changed',
                    'field': 'entity_type',
                    'from_value': from_entity['entity_type'],
                    'to_value': to_entity['entity_type']
                })
            
            # Compare details
            detail_changes = DiffService._compare_details(
                entity_uid,
                from_entity.get('details', []),
                to_entity.get('details', [])
            )
            changes.extend(detail_changes)
        
        return changes
    
    @staticmethod
    def _compare_details(entity_uid: str, from_details: List[Dict], to_details: List[Dict]) -> List[Dict[str, Any]]:
        """Compare detail lists and return changes."""
        changes = []
        
        # Create lookup dictionaries by detail_type
        from_details_map = {d['detail_type']: d for d in from_details}
        to_details_map = {d['detail_type']: d for d in to_details}
        
        # Find all detail types that existed in either snapshot
        all_detail_types = set(from_details_map.keys()) | set(to_details_map.keys())
        
        for detail_type in all_detail_types:
            from_detail = from_details_map.get(detail_type)
            to_detail = to_details_map.get(detail_type)
            
            if from_detail is None and to_detail is not None:
                # Detail added
                changes.append({
                    'entity_uid': entity_uid,
                    'change_type': 'detail_added',
                    'field': f'detail_{detail_type}',
                    'from_value': None,
                    'to_value': to_detail['detail_value']
                })
            elif from_detail is not None and to_detail is None:
                # Detail removed
                changes.append({
                    'entity_uid': entity_uid,
                    'change_type': 'detail_removed',
                    'field': f'detail_{detail_type}',
                    'from_value': from_detail['detail_value'],
                    'to_value': None
                })
            elif from_detail is not None and to_detail is not None:
                # Detail potentially changed
                if from_detail['detail_value'] != to_detail['detail_value']:
                    changes.append({
                        'entity_uid': entity_uid,
                        'change_type': 'detail_changed',
                        'field': f'detail_{detail_type}',
                        'from_value': from_detail['detail_value'],
                        'to_value': to_detail['detail_value']
                    })
        
        return changes
=======
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
>>>>>>> main
