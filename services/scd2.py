from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from typing import Dict, Any, Optional, Type
from django.db import models


class SCD2Service:
    """
    Service for handling SCD2 (Slowly Changing Dimension Type 2) update operations.
    Implements close-and-open logic for updating versioned records.
    
    Works with any Django model that has the following fields:
    - valid_from: DateTimeField
    - valid_to: DateTimeField (nullable)
    - is_current: BooleanField
    - A unique identifier field (e.g., entity_uid)
    """
    
    @classmethod
    @transaction.atomic
    def update_record(cls, model_class: Type[models.Model], uid_field: str, 
                     uid_value: Any, data: Dict[str, Any], 
                     timestamp: Optional[timezone.datetime] = None) -> models.Model:
        """
        Update an SCD2 record using close-and-open logic.
        
        Args:
            model_class: Django model class
            uid_field: Name of the unique identifier field
            uid_value: Value of the unique identifier
            data: Dictionary containing updated field values
            timestamp: Optional timestamp for the operation (defaults to now)
            
        Returns:
            New current record instance
            
        Raises:
            ValidationError: If no current record exists
        """
        if timestamp is None:
            timestamp = timezone.now()
            
        # Find current record
        current_record = cls.get_current_record(model_class, uid_field, uid_value)
        if not current_record:
            raise ValidationError(f"No current record found for {uid_field}={uid_value}")
        
        # Check if data actually changed (using hashdiff if available)
        if hasattr(current_record, 'hashdiff'):
            # Create temporary instance to compute hashdiff
            temp_data = {}
            for field in model_class._meta.fields:
                if field.name not in ['id', 'valid_from', 'valid_to', 'is_current', 'created_at', 'updated_at', 'hashdiff']:
                    if field.name in data:
                        temp_data[field.name] = data[field.name]
                    else:
                        temp_data[field.name] = getattr(current_record, field.name)
            
            temp_instance = model_class(**temp_data)
            temp_instance.save = lambda *args, **kwargs: None  # Prevent actual save
            temp_instance.save()  # This will compute hashdiff
            
            if temp_instance.hashdiff == current_record.hashdiff:
                # No actual change, return current record
                return current_record
        
        # Close current record
        current_record.valid_to = timestamp
        current_record.is_current = False
        current_record.save(update_fields=['valid_to', 'is_current'])
        
        # Create new record with updated data
        new_data = {}
        # Copy all fields from current record
        for field in model_class._meta.fields:
            if field.name not in ['id', 'valid_from', 'valid_to', 'is_current', 'created_at', 'updated_at']:
                new_data[field.name] = getattr(current_record, field.name)
        
        # Apply updates
        new_data.update(data)
        
        # Set SCD2 fields for new record
        new_data.update({
            'valid_from': timestamp,
            'valid_to': None,
            'is_current': True
        })
        
        # Create new current record
        new_record = model_class(**new_data)
        new_record.save()
        
        return new_record
    
    @classmethod
    def get_current_record(cls, model_class: Type[models.Model], uid_field: str, uid_value: Any) -> Optional[models.Model]:
        """
        Get the current record for a given unique identifier.
        
        Args:
            model_class: Django model class
            uid_field: Name of the unique identifier field
            uid_value: Value of the unique identifier
            
        Returns:
            Current record instance or None if not found
        """
        try:
            return model_class.objects.get(**{uid_field: uid_value, 'is_current': True})
        except model_class.DoesNotExist:
            return None
    
    @classmethod
    def get_as_of_record(cls, model_class: Type[models.Model], uid_field: str, 
                        uid_value: Any, as_of_date: timezone.datetime) -> Optional[models.Model]:
        """
        Get the record that was current at a specific point in time.
        
        Args:
            model_class: Django model class
            uid_field: Name of the unique identifier field
            uid_value: Value of the unique identifier
            as_of_date: The point in time to query
            
        Returns:
            Record instance that was current at as_of_date or None if not found
        """
        try:
            return model_class.objects.filter(
                **{uid_field: uid_value}
            ).filter(
                valid_from__lte=as_of_date
            ).filter(
                models.Q(valid_to__isnull=True) | models.Q(valid_to__gt=as_of_date)
            ).first()
        except model_class.DoesNotExist:
            return None
    
    @classmethod
    def get_history(cls, model_class: Type[models.Model], uid_field: str, uid_value: Any) -> models.QuerySet:
        """
        Get all historical records for a given unique identifier.
        
        Args:
            model_class: Django model class
            uid_field: Name of the unique identifier field
            uid_value: Value of the unique identifier
            
        Returns:
            QuerySet of all records ordered by valid_from desc
        """
        return model_class.objects.filter(
            **{uid_field: uid_value}
        ).order_by('-valid_from')