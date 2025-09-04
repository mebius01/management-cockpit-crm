from django.db import models


class EntityType(models.Model):
    """
    Defines the type of an entity (PERSON, INSTITUTION).
    """
    code = models.CharField(max_length=50, primary_key=True, help_text="Unique code for entity type.")
    name = models.CharField(max_length=255, help_text="Full name of the entity type.")
    description = models.TextField(blank=True, help_text="Optional description.")
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.code} ({self.name})"

class DetailType(models.Model):
    """
    Controlled vocabulary of detail types (EMAIL, PHONE, etc.).
    """
    code = models.CharField(max_length=50, primary_key=True, help_text="Unique code for the detail type.")
    name = models.CharField(max_length=255, help_text="Human-friendly name.")
    description = models.TextField(blank=True, help_text="Optional description.")
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.code} ({self.name})"
