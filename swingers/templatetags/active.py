"""
Maps request path to navigation urls to allow for "active" navigation links.

Taken from http://stackoverflow.com/a/656328, as a suggestion.
"""
from django import template

register = template.Library()

@register.tag
def active(parser, token):
    import re
    args = token.split_contents()
    template_tag = args[0]
    if len(args) < 2:
        # raise template.TemplateSyntaxError, "%r tag requires at least one argument." % template_tag
        raise template.TemplateSyntaxError("%r tag requires at least one argument." % template_tag)
    return NavSelectedNode(args[1:])

class NavSelectedNode(template.Node):
    def __init__(self, patterns):
        self.patterns = patterns

    def render(self, context):
        path = context['request'].path
        for p in self.patterns:
            value = template.Variable(p).resolve(context)
            if path == value:
                return "active"
        return ""
