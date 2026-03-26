from django.forms import widgets
from django.utils.safestring import mark_safe

class NumberInput(widgets.TextInput):
    input_type = 'number'

class LocationWidget(widgets.MultiWidget):

    DIRECTION_CHOICES = (
        ('','---'),
        ('N', 'N'),
        ('NNE', 'NNE'),
        ('NE', 'NE'),
        ('ENE', 'ENE'),
        ('E', 'E'),
        ('ESE', 'ESE'),
        ('SE', 'SE'),
        ('SSE', 'SSE'),
        ('S', 'S'),
        ('SSW', 'SSW'),
        ('SW', 'SW'),
        ('WSW', 'WSW'),
        ('W', 'W'),
        ('WNW', 'WNW'),
        ('NW', 'NW'),
        ('NNW', 'NNW'),
    )

    def __init__(self, attrs=None):
        _widgets = (
            widgets.TextInput(attrs={'class':'locn_locality'}),
            NumberInput(attrs={'class':'locn_distance', 'maxlength':'4'}),
            widgets.Select(attrs={'class':'locn_direction'}, choices=LocationWidget.DIRECTION_CHOICES),
            widgets.TextInput(attrs={'class':'locn_town'}),
        )
        super(LocationWidget, self).__init__(_widgets, attrs)

    def decompress(self, value):
        if value:
            value = value.split('|')
            if len(value) > 1:
                return [value[0] or None, value[1] or None, value[2] or None, value[3] or None]
            else:
                try:
                    value[0].split("Within the locality of ")[1]
                    return [value[0].split("Within the locality of ")[1],
                            None, None, None]
                except IndexError:
                    # Can't parse the string correctly, fall back to just using
                    # the value.
                    return [value[0], None, None, None]
        return [None, None, None, None]

    # def format_output(self, rendered_widgets):
    #     return rendered_widgets[0] + ' - ' + rendered_widgets[1] + 'km(s) ' + rendered_widgets[2] + ' of ' + rendered_widgets[3]


    def render(self, name, value, attrs=None, renderer=None): 
        value = self.decompress(value) 
        widgets_html = [ w.render(f"{name}_{i}", value[i], attrs, renderer) for i, w in enumerate(self.widgets) ] 
        return mark_safe( widgets_html[0] + " - " + widgets_html[1] + "km(s) " + widgets_html[2] + " of " + widgets_html[3] )
