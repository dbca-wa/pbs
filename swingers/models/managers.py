from django.db import models
from django.db.models.query import QuerySet
from django.db.models.sql.query import Query

from django.contrib.gis.db import models as geo_models
# from django.contrib.gis.db.models.query import GeoQuerySet
# from django.contrib.gis.db.models.sql.query import GeoQuery
from django.db.models import Q, QuerySet

import copy


class ActiveQuerySet(QuerySet):
    def __init__(self, model, query=None, using=None):
        # the model needs to be defined so that we can construct our custom
        # query
        if query is None:
            query = Query(model)
            query.add_q(models.Q(effective_to__isnull=True))
        return super(ActiveQuerySet, self).__init__(model, query, using)

    def __deepcopy__(self, memo):
        # borrowed from django.db.models.query.QuerySet because we need to pass
        # self.model to the self.__class__ call
        obj = self.__class__(self.model)
        for k, v in self.__dict__.items():
            if k in ('_iter', '_result_cache'):
                obj.__dict__[k] = None
            else:
                obj.__dict__[k] = copy.deepcopy(v, memo)
                return obj

    def delete(self):
        # see django.db.models.query.QuerySet.delete
        assert_msg = "Cannot use 'limit' or 'offset' with delete."
        assert self.query.can_filter(), assert_msg

        del_query = self._clone()
        del_query._for_write = True

        # Disable non-supported fields.
        del_query.query.select_for_update = False
        del_query.query.select_related = False
        del_query.query.clear_ordering(force_empty=True)

        # TODO: this could probably be made more efficient via the django
        # Collector, maybe
        for obj in del_query:
            obj.delete()

        # Clear the result cache, in case this QuerySet gets reused.
        self._result_cache = None
    delete.alters_data = True


#Original before python3 upgrade
# class ActiveGeoQuerySet(ActiveQuerySet, GeoQuerySet):
#     def __init__(self, model, query=None, using=None):
#         # the model needs to be defined so that we can construct our custom
#         # query
#         if query is None:
#             query = GeoQuery(model)
#             query.add_q(geo_models.Q(effective_to__isnull=True))
#         return super(ActiveGeoQuerySet, self).__init__(model, query, using)

class ActiveGeoQuerySet(ActiveQuerySet):
   def __init__(self, model=None, query=None, using=None):
       # the model needs to be defined so that we can construct our custom query
       if query is None:
           query = QuerySet(model)
           query = query.filter(Q(effective_to__isnull=True))
       super().__init__(model=model, query=query.query, using=using)



class ActiveModelManager(models.Manager):
    '''Exclude inactive ("deleted") objects from the query set.'''
    def get_query_set(self):
        '''Override the default queryset to filter out deleted objects.
        '''
        return ActiveQuerySet(self.model)

    # __getattr__ borrowed from
    # http://lincolnloop.com/django-best-practices/applications.html#managers
    def __getattr__(self, attr, *args):
        # see https://code.djangoproject.com/ticket/15062 for
        # details
        if attr.startswith("_"):
            raise AttributeError
        return getattr(self.get_query_set(), attr, *args)


#Original before python3 upgrade
# class ActiveGeoModelManager(ActiveModelManager, geo_models.GeoManager):
#     def get_query_set(self):
#         return ActiveGeoQuerySet(self.model)

class ActiveGeoModelManager(ActiveModelManager, models.Manager):
    def get_queryset(self):
        return ActiveGeoQuerySet(self.model, using=self._db)