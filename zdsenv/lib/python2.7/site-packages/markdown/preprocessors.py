"""
PRE-PROCESSORS
=============================================================================

Preprocessors work on source text before we start doing anything too
complicated.
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from . import util
from . import odict
import re


def build_preprocessors(md_instance):
    """ Build the default set of preprocessors used by Markdown. """
    preprocessors = odict.OrderedDict()
    preprocessors['normalize_whitespace'] = NormalizeWhitespace(md_instance)
    return preprocessors


class Preprocessor(util.Processor):
    """
    Preprocessors are run after the text is broken into lines.

    Each preprocessor implements a "run" method that takes a pointer to a
    list of lines of the document, modifies it as necessary and returns
    either the same pointer or a pointer to a new list.

    Preprocessors must extend markdown.Preprocessor.

    """

    def run(self, lines):
        """
        Each subclass of Preprocessor should override the `run` method, which
        takes the document as a list of strings split by newlines and returns
        the (possibly modified) list of lines.

        """
        pass  # pragma: no cover


class NormalizeWhitespace(Preprocessor):
    """ Normalize whitespace for consistant parsing. """

    def run(self, lines):
        source = '\n'.join(lines)
        source = source.replace(util.STX, "").replace(util.ETX, "")
        source = source.replace("\r\n", "\n").replace("\r", "\n") + "\n\n"
        source = source.expandtabs(self.markdown.tab_length)
        source = re.sub(r'(?<=\n) +\n', '\n', source)
        return source.split('\n')
