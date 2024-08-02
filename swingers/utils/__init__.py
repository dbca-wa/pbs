from __future__ import (division, print_function, unicode_literals,
                        absolute_import)
from django.template.defaultfilters import slugify

from itertools import chain, islice
from unidecode import unidecode

import binascii
import struct
import string
import random
import textwrap
import datetime
import time
import hashlib

# TODO: consider splitting this into utils.text, utils.generate, etc.


def machine_id():
    """Return a unique machine id that survives reboot and SW upgrades.

    Uses /proc/cpuinfo because /var/lib/dbus/machine-id is the same for all
    docker images that inherit/extend the same base image. Also, anybody that
    have access to any of those images can read the machine-id.
    """
    # take only certain lines from /proc/cpuinfo (assume new kernels may
    # add/change/remove stuff
    cpuinfo = [line for line
               in sorted(open('/proc/cpuinfo', 'r').readlines())
               if (line.startswith('processor') or
                   line.startswith('vendor_id') or
                   line.startswith('microcode'))]
    machine_id = hashlib.md5("".join(cpuinfo)).hexdigest()

    return slugify(machine_id)


def smart_truncate(content, length=100, suffix='...(more)'):
    '''
    Small function to truncate a string in a sensible way, sourced from:
    http://stackoverflow.com/questions/250357/smart-truncate-in-python
    '''
    if len(content) <= length:
        return content
    else:
        return ' '.join(content[:length + 1].split(' ')[0:-1]) + suffix


def label_span(text, label_class=None):
    '''
    Return a Bootstrap span class for inline-labelled text.
    Pass in a valid Bootstrap label class as a string, if required.
    '''
    if label_class in ['success', 'warning', 'important', 'info', 'inverse']:
        return '<span class="label label-{0}">{1}</span>'.format(label_class,
                                                                 text)
    else:
        return '<span class="label">{0}</span>'.format(text)


def breadcrumb_trail(links, sep=' > '):
    """
    ``links`` must be a list of two-item tuples in the format (URL, Text).
    URL may be None, in which case the trail will contain the Text only.
    Returns a string of HTML.
    """
    trail = ''
    url_str = '<a href="{0}">{1}</a>'
    # Iterate over the list, except for the last item.
    for i in links[:-1]:
        if i[0]:
            print(i)
            trail += url_str.format(i[0], i[1]) + sep
        else:
            trail += i[1] + sep
    # Add the list item on the list to the trail.
    if links[-1][0]:
        trail += url_str.format(links[-1][0], links[-1][1])
    else:
        trail += links[-1][1]
    return trail


def breadcrumbs_bootstrap(links, sep='>'):
    """
    Creates a breadcrumb trail in much the same way as `breadcrumb_trail`
    but formats it in the expected way for twitter bootstrap.
    """
    trail = ''
    url_str = '<a href="{0}">{1}</a>'
    sep_str = '<span class="divider">{0}</span>'
    # Iterate over the list, except for the last item.
    for i in links[:-1]:
        trail += '<li>'
        if i[0]:
            trail += url_str.format(i[0], i[1]) + sep_str.format(sep)
        else:
            trail += i[1] + sep_str.format(sep)
        trail += '</li>'
    # Add the list item on the list to the trail.
    trail += '<li class="active">'
    if links[-1][0]:
        trail += url_str.format(links[-1][0], links[-1][1])
    else:
        trail += links[-1][1]
    trail += '</li>'
    return trail


def timedcall(fn, *args, **kwargs):
    """
    Call function with args; return the time in seconds and result.
    """
    t0 = time.clock()
    result = fn(*args, **kwargs)
    t1 = time.clock()
    return t1 - t0, result


def content_filename(instance, filename):
    '''
    Decode unicode characters in file uploaded to ASCII-equivalents.
    Also replace spaces with underscores.

    This is to be passed to
    :class:`~django.db.models.fields.FileField.upload_to`,
    the `instance` parameter is unused.
    '''
    from datetime import datetime
    path = 'uploads/{date}/{filename}'
    filename = unidecode(filename).replace(' ', '_')
    d = {
        'date': datetime.strftime(datetime.today(), '%Y/%m/%d'),
        'filename': filename
    }
    return path.format(**d)


def sanitise_filename(f):
    """
    Take a string, and return it without special characters, and spaces
    replaced by underscores.
    """
    valid_chars = '-_. {0}{1}'.format(string.letters, string.digits)
    f = ''.join(c for c in f if c in valid_chars)
    return f.replace(' ', '_')


def shorthash(obj):
    """a 10-character hash of an arbitrary object."""
    sh = slugify(binascii.b2a_base64(struct.pack('l', hash(obj)))[:-2])
    if len(sh) > 10:
        return sh[:10]
    else:
        return sh.rjust(10, '0')


def get_random_datetime(year=random.choice(
        range(datetime.datetime.today().year - 5,
               datetime.datetime.today().year + 5))):
    """Return a random datetime object (year can be optionally specified).

    - use get_random_datetime().date() to get a random date object."""
    choice = lambda x: random.choice(range(1, x))
    return datetime.datetime(year, choice(12), choice(27), choice(24),
                             choice(60), choice(60))


def chomsky(times=1, line_length=100):
    """CHOMSKY is an aid to writing linguistic papers in the style
    of the great master.  It is based on selected phrases taken
    from actual books and articles written by Noam Chomsky.
    Upon request, it assembles the phrases in the elegant
    stylistic patterns that Chomsky is noted for.

    Specifically, we use it to generate semi-legible blocks of nonsense text
    phrases.

    @param times Number of sentences in the generated text.
    @param line_length  Wraps the lines of text within the line_length.
    """
    parts = []
    for part in (LEADINS, SUBJECTS, VERBS, OBJECTS):
        phraselist = map(lambda x: x.strip(), part.splitlines())
        random.shuffle(phraselist)
        parts.append(phraselist)
    output = chain(*islice(zip(*parts), 0, times))
    return textwrap.fill(' '.join(output), line_length)

LEADINS = """To characterize a linguistic level L,
On the other hand,
This suggests that
It appears that
Furthermore,
We will bring evidence in favor of the following thesis:
To provide a constituent structure for T(Z,K),
From C1, it follows that
For any transformation which is sufficiently diversified in application to be of any interest,
Analogously,
Clearly,
Note that
Of course,
Suppose, for instance, that
Thus
With this clarification,
Conversely,
We have already seen that
By combining adjunctions and certain deformations,
I suggested that these results would follow from the assumption that
If the position of the trace in (99c) were only relatively inaccessible to movement,
However, this assumption is not correct, since
Comparing these examples with their parasitic gap counterparts in (96) and (97), we see that
In the discussion of resumptive pronouns following (81),
So far,
Nevertheless,
For one thing,
Summarizing, then, we assume that
A consequence of the approach just outlined is that
Presumably,
On our assumptions,
It may be, then, that
It must be emphasized, once again, that
Let us continue to suppose that
Notice, incidentally, that """

SUBJECTS = """ the notion of level of grammaticalness
a case of semigrammaticalness of a different sort
most of the methodological work in modern linguistics
a subset of English sentences interesting on quite independent grounds
the natural general principle that will subsume this case
an important property of these three types of EC
any associated supporting element
the appearance of parasitic gaps in domains relatively inaccessible to ordinary extraction
the speaker-hearer's linguistic intuition
the descriptive power of the base component
the earlier discussion of deviance
this analysis of a formative as a pair of sets of features
this selectionally introduced contextual feature
a descriptively adequate grammar
the fundamental error of regarding functional notions as categorial
relational information
the systematic use of complex symbols
the theory of syntactic features developed earlier"""

VERBS = """can be defined in such a way as to impose
delimits
suffices to account for
cannot be arbitrary in
is not subject to
does not readily tolerate
raises serious doubts about
is not quite equivalent to
does not affect the structure of
may remedy and, at the same time, eliminate
is not to be considered in determining
is to be regarded as
is unspecified with respect to
is, apparently, determined by
is necessary to impose an interpretation on
appears to correlate rather closely with
is rather different from"""

OBJECTS = """ problems of phonemic and morphological analysis.
a corpus of utterance tokens upon which conformity has been defined by the paired utterance test.
the traditional practice of grammarians.
a stipulation to place the constructions into these various categories.
a descriptive fact.
a parasitic gap construction.
the extended c-command discussed in connection with (34).
the ultimate standard that determines the accuracy of any proposed grammar.
the system of base rules exclusive of the lexicon.
irrelevant intervening contexts in selectional rules.
nondistinctness in the sense of distinctive feature theory.
a general convention regarding the forms of the grammar.
an abstract underlying order.
an important distinction in language use.
the requirement that branching is not tolerated within the dominance scope of a complex symbol.
the strong generative capacity of the theory."""
