from django.contrib.admin import filters
from django.db import models
from django.contrib.admin.utils import (get_model_from_relation,)
from django.forms import ValidationError
from django.contrib.admin.options import IncorrectLookupParameters

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


def _to_bool(v):
    """Convert various representations to a bool or None.

    Handles strings, lists/tuples (takes first element), and other
    python values. Returns None for empty string or empty list.
    """
    # If it's a list or tuple, use the first element or "" if empty.
    if isinstance(v, (list, tuple)):
        v = v[0] if len(v) else ""
    if v == "":
        return None
    if isinstance(v, str):
        vl = v.lower()
        if vl in ("1", "true", "yes", "on"):
            return True
        if vl in ("0", "false", "no", "off"):
            return False
        # Non-empty string that isn't explicitly boolean-like is True
        return True
    return True if v else False

class BooleanFieldListFilter(filters.BooleanFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg1 = '%s' % field_path
        self.lookup_kwarg3 = '%s__in' % field_path
        self.lookup_val1 = request.GET.get(self.lookup_kwarg1, None)
        self.lookup_val3 = request.GET.get(self.lookup_kwarg3, None)
        super(BooleanFieldListFilter,self).__init__(field,request, params, model, model_admin, field_path)
        self.is_nullable = isinstance(self.field, models.NullBooleanField)

        def _to_bool(v):
            """Convert various representations to a bool or None.

            Handles strings, lists/tuples (takes first element), and other
            python values. Returns None for empty string or empty list.
            """
            # If it's a list or tuple, use the first element or "" if empty.
            if isinstance(v, (list, tuple)):
                v = v[0] if len(v) else ""
            if v == "":
                return None
            if isinstance(v, str):
                vl = v.lower()
                if vl in ("1", "true", "yes", "on"):
                    return True
                if vl in ("0", "false", "no", "off"):
                    return False
                # Non-empty string that isn't explicitly boolean-like is True
                return True
            return True if v else False
        for kwarg in (self.lookup_kwarg,self.lookup_kwarg1):
            if kwarg in self.used_parameters:
                val = _to_bool(self.used_parameters[kwarg])
                if val is None:
                    del self.used_parameters[kwarg]
                else:
                    self.used_parameters[kwarg] = [val]


        if self.lookup_kwarg3 in self.used_parameters:
            if isinstance(self.used_parameters[self.lookup_kwarg3],(list,tuple)):
                vals = None
                for v in self.used_parameters[self.lookup_kwarg3]:
                    val = _to_bool(v)
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
                    self.used_parameters[self.lookup_kwarg] = [vals[0]]
                elif self.is_nullable:
                    self.used_parameters[self.lookup_kwarg3] = vals
                else:
                    del self.used_parameters[self.lookup_kwarg3]
            else:
                val = _to_bool(self.used_parameters[self.lookup_kwarg3])
                if val is None:
                    del self.used_parameters[self.lookup_kwarg3]
                else:
                    del self.used_parameters[self.lookup_kwarg3]
                    self.used_parameters[self.lookup_kwarg] = [val]

    def expected_parameters(self):
        return [self.lookup_kwarg,self.lookup_kwarg1, self.lookup_kwarg2,self.lookup_kwarg3]

class CrossTenureApprovedListFilter(ExcludeListFilterMixin,BooleanFieldListFilter):
    def expected_parameters(self):
        # Ensure Django admin recognizes all possible filter params
        return [self.lookup_kwarg, self.lookup_kwarg1, self.lookup_kwarg3]

    def get_expected_value(self, value):
        # Normalize value for queryset filtering
        if value in (True, '1', 1, [True], ['1'], [1]):
            return True
        if value in (False, '0', 0, [False], ['0'], [0]):
            return False
        if value in (None, '', [None], ['']):
            return None
        return value

    def get_filter_value(self):
        # Try all possible parameter keys for this filter
        for key in (self.lookup_kwarg, self.lookup_kwarg1, self.lookup_kwarg3):
            val = self.used_parameters.get(key)
            if val is not None:
                # If it's a list, get the first value
                if isinstance(val, (list, tuple)):
                    if val:
                        return val[0]
                else:
                    return val
        return None

    def queryset(self, request, queryset):
        # Apply correct filter for admin list
        value = self.get_filter_value()
        value = self.get_expected_value(value)
        if value is True:
            return queryset.filter(non_calm_tenure_approved=True)
        elif value is False:
            return queryset.filter(non_calm_tenure_approved=False)
        elif value is None:
            return queryset.filter(non_calm_tenure_approved__isnull=True)
        return queryset
    def __init__(self, field, request, params, model, model_admin, field_path):
        super(CrossTenureApprovedListFilter, self).__init__(field, request, params, model, model_admin, field_path)
        self.used_parameters_exclude = {}
        # Fix for Django 3+: ensure all values are lists and handle string/boolean/null correctly
        for kwarg in (self.lookup_kwarg, self.lookup_kwarg1):
            if kwarg in self.used_parameters:
                val = self.used_parameters[kwarg]
                # Accept both boolean and string representations
                if val in (False, '0', 0, [False], ['0'], [0]):
                    self.used_parameters_exclude[kwarg] = [True]
                    del self.used_parameters[kwarg]
                elif val in (True, '1', 1, [True], ['1'], [1]):
                    self.used_parameters[kwarg] = [True]
                else:
                    # If null/None/empty string, treat as isnull
                    if val in (None, '', [None], ['']):
                        self.used_parameters[kwarg] = [None]
                    else:
                        self.used_parameters[kwarg] = [val]

        if self.lookup_kwarg3 in self.used_parameters:
            vals = self.used_parameters[self.lookup_kwarg3]
            if not isinstance(vals, (list, tuple)):
                vals = [vals]
            vals_set = set(str(v).lower() for v in vals)
            if 'false' in vals_set or '0' in vals_set:
                if 'true' in vals_set or '1' in vals_set:
                    del self.used_parameters[self.lookup_kwarg3]
                else:
                    self.used_parameters_exclude[self.lookup_kwarg] = [True]
                    del self.used_parameters[self.lookup_kwarg3]
            elif 'true' in vals_set or '1' in vals_set:
                self.used_parameters[self.lookup_kwarg] = [True]
                del self.used_parameters[self.lookup_kwarg3]
            elif '' in vals_set or 'none' in vals_set:
                self.used_parameters[self.lookup_kwarg] = [None]
                del self.used_parameters[self.lookup_kwarg3]


class IntChoicesFieldListFilter(filters.ChoicesFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg1 = '%s' % field_path
        self.lookup_val1 = request.GET.get(self.lookup_kwarg1, None)
        self.lookup_kwarg2 = '%s__in' % field_path
        self.lookup_val2 = request.GET.get(self.lookup_kwarg2, None)
        super(IntChoicesFieldListFilter,self).__init__(field,request, params, model, model_admin, field_path)
        to_int = lambda v :None if v == "" else (int(v[0]) if len(v) else None) if isinstance(v, (list, tuple,)) else int(v)
        
        for kwarg in (self.lookup_kwarg,self.lookup_kwarg1):
            if kwarg in self.used_parameters:
                val = to_int(self.used_parameters[kwarg])
                if val is None:
                    del self.used_parameters[kwarg]
                else:
                    self.used_parameters[kwarg] = [val]


        if self.lookup_kwarg2 in self.used_parameters:
            used_params = self.used_parameters[self.lookup_kwarg2]
            if isinstance(used_params,(list,tuple)):
                if len(used_params) > 0 and isinstance(used_params[0],(list,tuple)):
                    self.used_parameters[self.lookup_kwarg2] = [v for sublist in used_params for v in sublist]
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
                    self.used_parameters[self.lookup_kwarg] = vals
                else:
                    self.used_parameters[self.lookup_kwarg2] = [vals]
            else:
                val = to_int(self.used_parameters[self.lookup_kwarg2])
                if val is None:
                    del self.used_parameters[self.lookup_kwarg2]
                else:
                    del self.used_parameters[self.lookup_kwarg2]
                    self.used_parameters[self.lookup_kwarg] = [val]


    def expected_parameters(self):
        return [self.lookup_kwarg,self.lookup_kwarg1, self.lookup_kwarg2]



class RelatedFieldListFilterOriginal(filters.RelatedFieldListFilter):
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
                    self.used_parameters[self.lookup_kwarg] = [vals[0]]
                else:
                    self.used_parameters[self.lookup_kwarg2] = vals
            else:
                val = to_int(self.used_parameters[self.lookup_kwarg2])
                if val is None:
                    del self.used_parameters[self.lookup_kwarg2]
                else:
                    del self.used_parameters[self.lookup_kwarg2]
                    self.used_parameters[self.lookup_kwarg] = [val]


    def expected_parameters(self):
        return [self.lookup_kwarg,self.lookup_kwarg1,self.lookup_kwarg2, self.lookup_kwarg_isnull]
    
class RelatedFieldListFilter(filters.RelatedFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        other_model = get_model_from_relation(field)
        if hasattr(field, 'rel'):
            rel_name = field.rel.get_related_field().name
        else:
            rel_name = other_model._meta.pk.name
        self.lookup_kwarg1 = '%s__%s' % (field_path, rel_name)
        self.lookup_val1 = request.GET.get(self.lookup_kwarg1, None)
        self.lookup_kwarg2 = '%s__%s__in' % (field_path, rel_name)
        self.lookup_val2 = request.GET.get(self.lookup_kwarg2, None)
        super(RelatedFieldListFilter, self).__init__(field, request, params, model, model_admin, field_path)
        # Lambda to convert value to int or None if it's invalid and handle list values
        to_int = lambda v: None if v in (None, "", False) else int(v[0]) if isinstance(v, list) else int(v)
        # Handle single value filters (non-__in lookups)
        for kwarg in (self.lookup_kwarg, self.lookup_kwarg1):
            if kwarg in self.used_parameters:
                val = to_int(self.used_parameters[kwarg])
                if val is None:
                    del self.used_parameters[kwarg]
                else:
                    self.used_parameters[kwarg] = [val]  # Keep the value as an integer
        # Handle __in lookups (multiple values)
        if self.lookup_kwarg2 in self.used_parameters:
            if isinstance(self.used_parameters[self.lookup_kwarg2], (list, tuple)):
                # vals = [to_int(v) for v in self.used_parameters[self.lookup_kwarg2] if to_int(v) is not None]
                vals = [to_int(v) for sublist in self.used_parameters[self.lookup_kwarg2] for v in sublist if to_int(v) is not None]
                if not vals:
                    del self.used_parameters[self.lookup_kwarg2]
                elif len(vals) == 1:
                    self.used_parameters[self.lookup_kwarg] = [vals[0]]
                    del self.used_parameters[self.lookup_kwarg2]
                else:
                    self.used_parameters[self.lookup_kwarg2] = [vals]
            else:
                val = to_int(self.used_parameters[self.lookup_kwarg2])
                if val is None:
                    del self.used_parameters[self.lookup_kwarg2]
                else:
                    self.used_parameters[self.lookup_kwarg] = [val]  # Wrap the single value in a list
                    del self.used_parameters[self.lookup_kwarg2]

    
    def expected_parameters(self):
        return [self.lookup_kwarg,self.lookup_kwarg1,self.lookup_kwarg2, self.lookup_kwarg_isnull]

class StringValuesFieldListFilter(filters.AllValuesFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg2 = '%s__in' % field_path
        self.lookup_val2 = request.GET.get(self.lookup_kwarg2, None)
        super(StringValuesFieldListFilter, self).__init__(field, request, params, model, model_admin, field_path)
        to_str = lambda v :None if v == "" else str(v) 
        for kwarg in (self.lookup_kwarg,):
            if kwarg in self.used_parameters:
                val = to_str(self.used_parameters[kwarg])
                if val is None:
                    del self.used_parameters[kwarg]
                else:
                    self.used_parameters[kwarg] = [val]


        if self.lookup_kwarg2 in self.used_parameters:
            used_params = self.used_parameters[self.lookup_kwarg2]
            if isinstance(used_params,(list,tuple)):
                if len(used_params) > 0 and isinstance(used_params[0],(list,tuple)):
                    self.used_parameters[self.lookup_kwarg2] = [v for sublist in used_params for v in sublist]

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
                    self.used_parameters[self.lookup_kwarg] = [vals[0]]
                else:
                    self.used_parameters[self.lookup_kwarg2] = [vals]
            else:
                val = to_str(self.used_parameters[self.lookup_kwarg2])
                if val is None:
                    del self.used_parameters[self.lookup_kwarg2]
                else:
                    del self.used_parameters[self.lookup_kwarg2]
                    self.used_parameters[self.lookup_kwarg] = [val]


    def expected_parameters(self):
        return [self.lookup_kwarg,self.lookup_kwarg2, self.lookup_kwarg_isnull]

