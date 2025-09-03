"""
Pytest configuration and shared fixtures for Management Cockpit CRM tests.
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

import pytest
import django
from django.conf import settings

# Configure Django settings before importing models
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.test_settings')
    django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from freezegun import freeze_time

from entity.models import EntityType, DetailType, Entity, EntityDetail


@pytest.fixture
def test_user() -> User:
    """Create a test user for authentication tests."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )


@pytest.fixture
def entity_type_person() -> EntityType:
    """Create PERSON entity type."""
    return EntityType.objects.create(
        code="PERSON",
        name="Person",
        description="Individual person",
        is_active=True
    )


@pytest.fixture
def entity_type_institution() -> EntityType:
    """Create INSTITUTION entity type."""
    return EntityType.objects.create(
        code="INSTITUTION",
        name="Institution",
        description="Organization or company",
        is_active=True
    )


@pytest.fixture
def current_time() -> datetime:
    """Fixed current time for consistent testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def freeze_current_time(current_time: datetime):
    """Freeze time to current_time for consistent testing."""
    with freeze_time(current_time):
        yield current_time


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass
