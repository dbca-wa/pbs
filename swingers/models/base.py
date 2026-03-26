from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from django.contrib.gis.db import models as geo_models
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django.db import router, models
from django.db.models import signals
from django.db.models.deletion import Collector


from swingers.models.managers import ActiveModelManager, ActiveGeoModelManager


class ActiveModel(models.Model):
    '''
    Model mixin to allow objects to be saved as 'non-current' or 'inactive',
    instead of deleting those objects.
    The standard model delete() method is overridden.

    "effective_from" allows 'past' and/or 'future' objects to be saved.
    "effective_to" is used to 'delete' objects (null==not deleted).
    '''
    effective_from = models.DateTimeField(default=timezone.now)
    effective_to = models.DateTimeField(null=True, blank=True)
    objects = ActiveModelManager()
    # Return all objects, including deleted ones, the default manager.
    objects_all = models.Manager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        if not issubclass(type(type(self).objects), ActiveModelManager):
            raise ImproperlyConfigured(
                "The ActiveModel objects manager is not a subclass of "
                "swingers.base.models.managers.ActiveModelManager, if you "
                "created your own objects manager, it must be a subclass of "
                "ActiveModelManager.")
        super(ActiveModel, self).__init__(*args, **kwargs)

    def is_active(self):
        return self.effective_to is None

    def is_deleted(self):
        return not self.is_active()

    def delete(self, *args, **kwargs):
        '''
        Overides the standard model delete method; sets "effective_to" as the
        current date and time and then calls save() instead.
        '''
        # see django.db.models.deletion.Collection.delete
        using = kwargs.get('using', router.db_for_write(self.__class__,
                                                        instance=self))
        cannot_be_deleted_assert = ("""%s object can't be deleted because its
                                    %s attribute is set to None.""" %
                                    (self._meta.object_name,
                                     self._meta.pk.attname))
        assert self._get_pk_val() is not None, cannot_be_deleted_assert
        collector = Collector(using=using)
        collector.collect([self])
        collector.sort()

        # send pre_delete signals
        def delete(collector):
            for model, obj in collector.instances_with_model():
                if not model._meta.auto_created:
                    signals.pre_delete.send(
                        sender=model, instance=obj, using=using
                    )

            # be compatible with django 1.4.x
            if hasattr(collector, 'fast_deletes'):
                # fast deletes
                for qs in collector.fast_deletes:
                    for instance in qs:
                        self._delete(instance)

            # delete batches
            # be compatible with django>=1.6
            if hasattr(collector, 'batches'):
                # for model, batches in six.iteritems(collector.batches):
                for model, batches in collector.batches.items():
                    # for field, instances in six.iteritems(batches):
                    for field, instances in batches.items():
                        for instance in instances:
                            self._delete(instance)

            # "delete" instances
            for model, instances in collector.data.items():
                for instance in instances:
                    self._delete(instance)

            # send post_delete signals
            for model, obj in collector.instances_with_model():
                if not model._meta.auto_created:
                    signals.post_delete.send(
                        sender=model, instance=obj, using=using
                    )

        # another django>=1.6 thing
        try:
            from django.db.transaction import commit_on_success_unless_managed
        except ImportError:
            delete(collector)
        else:
            commit_on_success_unless_managed(using=using)(delete(collector))

    delete.alters_data = True

    def _delete(self, instance):
        instance.effective_to = timezone.now()
        instance.save()


class ActiveGeoModel(ActiveModel):
    objects = ActiveGeoModelManager()
    # Return all objects, including deleted ones, the default manager.
    # objects_all = geo_models.GeoManager()
    objects_all = models.Manager()

    def __init__(self, *args, **kwargs):
        if not issubclass(type(type(self).objects), ActiveGeoModelManager):
            raise ImproperlyConfigured(
                "The ActiveGeoModel objects manager is not a subclass of "
                "swingers.base.models.models.ActiveGeoModelManager, if you "
                "created your own objects manager, it must be a subclass of "
                "ActiveGeoModelManager.")
        super(ActiveGeoModel, self).__init__(*args, **kwargs)

    class Meta:
        abstract = True
