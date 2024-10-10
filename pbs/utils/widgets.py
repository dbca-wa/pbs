from __future__ import unicode_literals

from itertools import chain

from django.forms.widgets import SelectMultiple, CheckboxInput
from django.utils.html import format_html
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe

# TODO: this code should work for Django 1.6
#
#class CheckboxFieldRenderer(widgets.CheckboxFieldRenderer):
#    def render(self):
#        output = []
#        for widget in self:
#            output.append(format_html(force_str(widget)))
#        return mark_safe('\n'.join(output))
#
#
#class CheckboxSelectMultiple(widgets.CheckboxSelectMultiple):
#    renderer = CheckboxFieldRenderer


# This code is from Django 1.5
class CheckboxSelectMultiple(SelectMultiple):
    def render(self, name, value, attrs=None, choices=(), renderer=None):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        # final_attrs = self.build_attrs(attrs, name=name)
        attrs['name'] = name
        final_attrs = self.build_attrs(attrs)
        output = []
        # Normalize to strings
        str_values = set([force_str(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = format_html(' for="{0}"', final_attrs['id'])
            else:
                label_for = ''

            cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_str(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = force_str(option_label)
            output.append(format_html('<label{0} class="checkbox">{1} {2}</label>',
                                      label_for, rendered_cb, option_label))
        return mark_safe('\n'.join(output))

    def id_for_label(self, id_):
        # See the comment for RadioSelect.id_for_label()
        if id_:
            id_ += '_0'
        return id_
