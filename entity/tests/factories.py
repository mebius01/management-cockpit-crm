import factory
from django.utils import timezone
from datetime import datetime, timedelta
from entity.models import Entity, EntityDetail, EntityType, DetailType


class EntityTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EntityType
        django_get_or_create = ('code',)
    
    code = factory.Sequence(lambda n: f"TYPE_{n}")
    name = factory.Faker('word')


class DetailTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DetailType
        django_get_or_create = ('code',)
    
    code = factory.Sequence(lambda n: f"DETAIL_{n}")
    name = factory.Faker('word')


class EntityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Entity
    
    display_name = factory.Faker('name')
    entity_type = factory.SubFactory(EntityTypeFactory)
    valid_from = factory.LazyFunction(timezone.now)
    is_current = True


class EntityDetailFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EntityDetail
    
    entity = factory.SubFactory(EntityFactory)
    detail_type = factory.SubFactory(DetailTypeFactory)
    detail_value = factory.Faker('text', max_nb_chars=100)
    valid_from = factory.LazyFunction(timezone.now)
    is_current = True
