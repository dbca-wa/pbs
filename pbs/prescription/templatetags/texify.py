from django.template.defaultfilters import stringfilter, register
from django.utils.safestring import mark_safe

REPLACEMENTS = {
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '<': r'\textless{}',
    '>': r'\textgreater',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\textasciicircum',
    '\n': r'\newline ',
    '\r': r'',
}

# TODO: Fix up Very Low/Low/Medium/High/Very High colours
COLOURUPS = {
    "Complete": "success",
    "Corporate Approved": "success",
    "Endorsed": "success",
    "Not Endorsed": "error",
    "Approved": "success",
    "Not Approved": "error",
    "No Ignitions": "muted",
    "Ignition Completed": "success",
    "Burn Open": "muted",
    "Burn Closed": "success",
    "Very Low": "verylow",
    "Low": "low",
    "Medium": "medium",
    "High": "high",
    "Very High": "veryhigh",
    "Incomplete": "error",
    "Not Applicable": "muted",
    "1": "success",
    "2": "success",
    "3": "warning",
    "4": "warning",
    "5": "error",
    "6": "error",
    "Rare": "success",
    "Unlikely": "success",
    "Possible": "warning",
    "Likely": "error",
    "Almost Certain": "error"
}


@register.filter
@stringfilter
def texify(value):
    """
    Escapes special LaTeX characters.
    """
    value = value.strip()
    for k, v in REPLACEMENTS.items():
        value = value.replace(k, v)
    return mark_safe(value)


@register.filter
@stringfilter
def colourise(value, background=False):
    """
    Colours standard words. If no color, defaults to Fuchsia.
    Background = true doesn't work outside of cells.
    """
    if background:
        return mark_safe("".join((r"\cellcolor{", COLOURUPS.get(value, "white"),
                         "}{", value, "}")))
    else:
        return mark_safe("".join((r"\textcolor{", COLOURUPS.get(value, "purple"),
                     "}{", value, "}")))
