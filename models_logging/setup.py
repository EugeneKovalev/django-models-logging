from uuid import uuid4

from django.apps.registry import apps
from django.db import router
from django.db.models import Model
from django.db.models.deletion import Collector
from django.db.models.query import QuerySet
from django.db.models.signals import post_init, post_save

from .settings import MODELS_FOR_LOGGING, MODELS_FOR_EXCLUDE
from .signals import init_model_attrs, save_model, delete_model


class LoggingQuerySet(QuerySet):

    def bulk_create(self, objs, **kwargs):
        instances = super().bulk_create(objs, **kwargs)

        uuid = uuid4().hex
        for instance in instances:
            save_model(
                sender=instance._meta.model,
                instance=instance,
                using=instance._state.db,
                created=True,
                uuid=uuid
            )

        return instances

    def update(self, *args, **kwargs):
        uuid = uuid4().hex
        for instance in list(self):
            for field, new_value in kwargs.items():
                setattr(instance, field, new_value)

            save_model(
                sender=instance._meta.model,
                instance=instance,
                using=instance._state.db,
                created=False,
                uuid=uuid
            )

        instances = super().update(*args, **kwargs)

        return instances

    def delete(self, *args, **kwargs):
        uuid = uuid4().hex
        for instance in list(self):
            delete_model(
                sender=instance._meta.model,
                instance=instance,
                using=instance._state.db,
                uuid=uuid
            )

        return super().delete(*args, **kwargs)


class LoggingModelMixin(object):
    def delete(self, using=None, keep_parents=False):
        delete_model(
            sender=self._meta.model,
            instance=self,
            using=self._state.db
        )

        using = using or router.db_for_write(self.__class__, instance=self)
        assert self.pk is not None, (
                "%s object can't be deleted because its %s attribute is set to None." %
                (self._meta.object_name, self._meta.pk.attname)
        )

        collector = Collector(using=using)
        collector.collect([self], keep_parents=keep_parents)
        return collector.delete()


def register(model):
    post_init.connect(init_model_attrs, sender=model)
    post_save.connect(save_model, sender=model)

    manager = LoggingQuerySet.as_manager()
    manager.contribute_to_class(model, 'objects')
    setattr(model, 'objects', manager)
    setattr(model, 'delete', LoggingModelMixin.delete)

    return model