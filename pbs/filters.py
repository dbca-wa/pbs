from django.contrib.admin import filters
from django.db import models
from django.contrib.admin.utils import (get_model_from_relation,)

class ExcludeListFilterMixin(object):
    def queryset(self, request, queryset):
        queryset = super(ExcludeListFilterMixin,self).queryset(request,queryset)
        try:
            if self.used_parameters_exclude:
                return queryset.exclude(**self.used_parameters_exclude)
            else:
                return queryset
        except ValidationError as e:
            raise IncorrectLookupParameters(e)

class BooleanFieldListFilter(filters.BooleanFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg1 = '%s' % field_path
        self.lookup_kwarg3 = '%s__in' % field_path
        self.lookup_val1 = request.GET.get(self.lookup_kwarg1, None)
        self.lookup_val3 = request.GET.get(self.lookup_kwarg3, None)
        super(BooleanFieldListFilter,self).__init__(field,request, params, model, model_admin, field_path)
        self.is_nullable = isinstance(self.field, models.NullBooleanField)

        to_bool = lambda v :(None if v == "" else (True if v in ("1","true","yes","on") else False)) if isinstance(v,basestring) else (True if v else False)
        for kwarg in (self.lookup_kwarg,self.lookup_kwarg1):
            if kwarg in self.used_parameters:
                val = to_bool(self.used_parameters[kwarg])
                if val is None:
                    del self.used_parameters[kwarg]
                else:
                    self.used_parameters[kwarg] = val


        if self.lookup_kwarg3 in self.used_parameters:
            if isinstance(self.used_parameters[self.lookup_kwarg3],(list,tuple)):
                vals = None
                for v in self.used_parameters[self.lookup_kwarg3]:
                    val = to_bool(v)
                    if val is None:
                        continue
                    if vals is None:
                        vals = [val]
                    elif val not in vals:
                        vals.append(val)
                if vals is None:
                    del self.used_parameters[self.lookup_kwarg3]
                elif len(vals) == 1:
                    del self.used_parameters[self.lookup_kwarg3]
                    self.used_parameters[self.lookup_kwarg] = vals[0]
                elif self.is_nullable:
                    self.used_parameters[self.lookup_kwarg3] = vals
                else:
                    del self.used_parameters[self.lookup_kwarg3]
            else:
                val = to_bool(self.used_parameters[self.lookup_kwarg3])
                if val is None:
                    del self.used_parameters[self.lookup_kwarg3]
                else:
                    del self.used_parameters[self.lookup_kwarg3]
                    self.used_parameters[self.lookup_kwarg] = val

    def expected_parameters(self):
        return [self.lookup_kwarg,self.lookup_kwarg1, self.lookup_kwarg2,self.lookup_kwarg3]

class CrossTenureApprovedListFilter(ExcludeListFilterMixin,BooleanFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super(CrossTenureApprovedListFilter,self).__init__(field,request, params, model, model_admin, field_path)
        self.used_parameters_exclude = {}
        for kwarg in (self.lookup_kwarg,self.lookup_kwarg1):
            if kwarg in self.used_parameters:
                if self.used_parameters[kwarg] == False:
                    self.used_parameters_exclude[kwarg] = True
                    del self.used_parameters[kwarg]

        if self.lookup_kwarg3 in self.used_parameters:
            if False in self.used_parameters[self.lookup_kwarg3] :
                if True in self.used_parameters[self.lookup_kwarg3] :
                    del self.used_parameters[self.lookup_kwarg3]
                else:
                    self.used_parameters_exclude[self.lookup_kwarg] = True
                    del self.used_parameters[self.lookup_kwarg3]
            else:
                self.used_parameters[self.lookup_kwarg] = True
                del self.used_parameters[self.lookup_kwarg3]


class IntChoicesFieldListFilter(filters.ChoicesFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg1 = '%s' % field_path
        self.lookup_val1 = request.GET.get(self.lookup_kwarg1, None)
        self.lookup_kwarg2 = '%s__in' % field_path
        self.lookup_val2 = request.GET.get(self.lookup_kwarg2, None)
        super(IntChoicesFieldListFilter,self).__init__(field,request, params, model, model_admin, field_path)
        to_int = lambda v :None if v == "" else int(v) 
        for kwarg in (self.lookup_kwarg,self.lookup_kwarg1):
            if kwarg in self.used_parameters:
                val = to_int(self.used_parameters[kwarg])
                if val is None:
                    del self.used_parameters[kwarg]
                else:
                    self.used_parameters[kwarg] = val


        if self.lookup_kwarg2 in self.used_parameters:
            if isinstance(self.used_parameters[self.lookup_kwarg2],(list,tuple)):
                vals = None
                for v in self.used_parameters[self.lookup_kwarg2]:
                    val = to_int(v)
                    if val is None:
                        continue
                    if vals is None:
                        vals = [val]
                    else:
                        vals.append(val)
                if vals is None:
                    del self.used_parameters[self.lookup_kwarg2]
                elif len(vals) == 1:
                    del self.used_parameters[self.lookup_kwarg2]
                    self.used_parameters[self.lookup_kwarg] = vals[0]
                else:
                    self.used_parameters[self.lookup_kwarg2] = vals
            else:
                val = to_int(self.used_parameters[self.lookup_kwarg2])
                if val is None:
                    del self.used_parameters[self.lookup_kwarg2]
                else:
                    del self.used_parameters[self.lookup_kwarg2]
                    self.used_parameters[self.lookup_kwarg] = val


    def expected_parameters(self):
        return [self.lookup_kwarg,self.lookup_kwarg1, self.lookup_kwarg2]



class RelatedFieldListFilter(filters.RelatedFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        other_model = get_model_from_relation(field)
        if hasattr(field, 'rel'):
            rel_name = field.rel.get_related_field().name
        else:
            rel_name = other_model._meta.pk.name

        self.lookup_kwarg1 = '%s__%s' % (field_path,rel_name)
        self.lookup_val1 = request.GET.get(self.lookup_kwarg1, None)

        self.lookup_kwarg2 = '%s__%s__in' % (field_path,rel_name)
        self.lookup_val2 = request.GET.get(self.lookup_kwarg2, None)

        super(RelatedFieldListFilter, self).__init__(field, request, params, model, model_admin, field_path)
        to_int = lambda v :None if v == "" else int(v) 
        for kwarg in (self.lookup_kwarg,self.lookup_kwarg1):
            if kwarg in self.used_parameters:
                val = to_int(self.used_parameters[kwarg])
                if val is None:
                    del self.used_parameters[kwarg]
                else:
                    self.used_parameters[kwarg] = val


        if self.lookup_kwarg2 in self.used_parameters:
            if isinstance(self.used_parameters[self.lookup_kwarg2],(list,tuple)):
                vals = None
                for v in self.used_parameters[self.lookup_kwarg2]:
                    val = to_int(v)
                    if val is None:
                        continue
                    if vals is None:
                        vals = [val]
                    else:
                        vals.append(val)
                if vals is None:
                    del self.used_parameters[self.lookup_kwarg2]
                elif len(vals) == 1:
                    del self.used_parameters[self.lookup_kwarg2]
                    self.used_parameters[self.lookup_kwarg] = vals[0]
                else:
                    self.used_parameters[self.lookup_kwarg2] = vals
            else:
                val = to_int(self.used_parameters[self.lookup_kwarg2])
                if val is None:
                    del self.used_parameters[self.lookup_kwarg2]
                else:
                    del self.used_parameters[self.lookup_kwarg2]
                    self.used_parameters[self.lookup_kwarg] = val


    def expected_parameters(self):
        return [self.lookup_kwarg,self.lookup_kwarg1,self.lookup_kwarg2, self.lookup_kwarg_isnull]

class IntValuesFieldListFilter(filters.AllValuesFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg2 = '%s__in' % field_path
        self.lookup_val2 = request.GET.get(self.lookup_kwarg2, None)
        super(IntValuesFieldListFilter, self).__init__(field, request, params, model, model_admin, field_path)
        to_int = lambda v :None if v == "" else int(v) 
        for kwarg in (self.lookup_kwarg,):
            if kwarg in self.used_parameters:
                val = to_int(self.used_parameters[kwarg])
                if val is None:
                    del self.used_parameters[kwarg]
                else:
                    self.used_parameters[kwarg] = val


        if self.lookup_kwarg2 in self.used_parameters:
            if isinstance(self.used_parameters[self.lookup_kwarg2],(list,tuple)):
                vals = None
                for v in self.used_parameters[self.lookup_kwarg2]:
                    val = to_int(v)
                    if val is None:
                        continue
                    if vals is None:
                        vals = [val]
                    else:
                        vals.append(val)
                if vals is None:
                    del self.used_parameters[self.lookup_kwarg2]
                elif len(vals) == 1:
                    del self.used_parameters[self.lookup_kwarg2]
                    self.used_parameters[self.lookup_kwarg] = vals[0]
                else:
                    self.used_parameters[self.lookup_kwarg2] = vals
            else:
                val = to_int(self.used_parameters[self.lookup_kwarg2])
                if val is None:
                    del self.used_parameters[self.lookup_kwarg2]
                else:
                    del self.used_parameters[self.lookup_kwarg2]
                    self.used_parameters[self.lookup_kwarg] = val


    def expected_parameters(self):
        return [self.lookup_kwarg,self.lookup_kwarg2, self.lookup_kwarg_isnull]

class StringValuesFieldListFilter(filters.AllValuesFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg2 = '%s__in' % field_path
        self.lookup_val2 = request.GET.get(self.lookup_kwarg2, None)
        super(StringValuesFieldListFilter, self).__init__(field, request, params, model, model_admin, field_path)
        to_str = lambda v :None if v == "" else str(v) 
        for kwarg in (self.lookup_kwarg,):
            if kwarg in self.used_parameters:
                val = to_int(self.used_parameters[kwarg])
                if val is None:
                    del self.used_parameters[kwarg]
                else:
                    self.used_parameters[kwarg] = val


        if self.lookup_kwarg2 in self.used_parameters:
            if isinstance(self.used_parameters[self.lookup_kwarg2],(list,tuple)):
                vals = None
                for v in self.used_parameters[self.lookup_kwarg2]:
                    val = to_str(v)
                    if val is None:
                        continue
                    if vals is None:
                        vals = [val]
                    else:
                        vals.append(val)
                if vals is None:
                    del self.used_parameters[self.lookup_kwarg2]
                elif len(vals) == 1:
                    del self.used_parameters[self.lookup_kwarg2]
                    self.used_parameters[self.lookup_kwarg] = vals[0]
                else:
                    self.used_parameters[self.lookup_kwarg2] = vals
            else:
                val = to_int(self.used_parameters[self.lookup_kwarg2])
                if val is None:
                    del self.used_parameters[self.lookup_kwarg2]
                else:
                    del self.used_parameters[self.lookup_kwarg2]
                    self.used_parameters[self.lookup_kwarg] = val


    def expected_parameters(self):
        return [self.lookup_kwarg,self.lookup_kwarg2, self.lookup_kwarg_isnull]

