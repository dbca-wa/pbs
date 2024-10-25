import itertools
from pbs.risk.models import Register
from django import template

register = template.Library()

class Counter(object):
    def __init__(self, start, step=1):
        self.count = itertools.count(start, step)

    def next(self):
        # return self.count.next()
        return next(self.count)

    def __iter__(self):
        return self

    # def __unicode__(self):
    #     return unicode(self.next())
    def __str__(self):
        return str(self.next())

@register.simple_tag
def counter_from(start, step=1):
    return Counter(int(start), int(step))
