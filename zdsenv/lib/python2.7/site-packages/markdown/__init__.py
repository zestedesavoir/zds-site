"""
Python Markdown
===============

Python Markdown converts Markdown to HTML and can be used as a library or
called from the command line.

## Basic usage as a module:

    import markdown
    html = markdown.markdown(your_text_string)

See <https://pythonhosted.org/Markdown/> for more
information and instructions on how to extend the functionality of
Python Markdown.  Read that before you try modifying this file.

## Authors and License

Started by [Manfred Stienstra](http://www.dwerg.net/).  Continued and
maintained  by [Yuri Takhteyev](http://www.freewisdom.org), [Waylan
Limberg](http://achinghead.com/) and [Artem Yunusov](http://blog.splyer.com).

Contact: markdown@freewisdom.org

Copyright 2007-2013 The Python Markdown Project (v. 1.7 and later)
Copyright 200? Django Software Foundation (OrderedDict implementation)
Copyright 2004, 2005, 2006 Yuri Takhteyev (v. 0.2-1.6b)
Copyright 2004 Manfred Stienstra (the original version)

License: BSD (see LICENSE for details).
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from .__version__ import version, version_info  # noqa
import logging
import warnings
import importlib
from . import util
from .preprocessors import build_preprocessors
from .blockprocessors import build_block_parser
from .treeprocessors import build_treeprocessors
from .inlinepatterns import build_inlinepatterns
from .postprocessors import build_postprocessors
from .extensions import Extension
from .serializers import to_html_string

__all__ = ['Markdown', 'markdown']

logger = logging.getLogger('MARKDOWN')


class Markdown(object):
    """Convert Markdown to HTML."""

    doc_tag = "div"  # Element used to wrap document - later removed

    option_defaults = {
        'tab_length': 4,
        'inline': False,
    }

    ESCAPED_CHARS = ['\\', '`', '*', '_', '{', '}', '[', ']',
                     '(', ')', '>', '#', '+', '-', '.', '!']

    def __init__(self, **kwargs):
        """
        Creates a new Markdown instance.

        Keyword arguments:

        * extensions: A list of extensions.
           If they are of type string, the module mdx_name.py will be loaded.
           If they are a subclass of markdown.Extension, they will be used
           as-is.
        * extension_configs: Configuration settings for extensions.
        * tab_length: Length of tabs in the source. Default: 4
        """

        self.metadata = {}

        # Loop through kwargs and assign defaults
        for option, default in self.option_defaults.items():
            setattr(self, option, kwargs.get(option, default))

        self.registeredExtensions = []
        self.docType = ""
        self.stripTopLevelTags = True

        self.build_parser()

        self.references = {}
        self.htmlStash = util.HtmlStash()
        self.registerExtensions(extensions=kwargs.get('extensions', []),
                                configs=kwargs.get('extension_configs', {}))
        self.serializer = to_html_string

        self.reset()

    def build_parser(self):
        """ Build the parser from the various parts. """
        self.preprocessors = build_preprocessors(self)
        self.parser = build_block_parser(self)
        self.inlinePatterns = build_inlinepatterns(self)
        self.treeprocessors = build_treeprocessors(self)
        self.postprocessors = build_postprocessors(self)
        return self

    def registerExtensions(self, extensions, configs):
        """
        Register extensions with this instance of Markdown.

        Keyword arguments:

        * extensions: A list of extensions, which can either
           be strings or objects.  See the docstring on Markdown.
        * configs: A dictionary mapping module names to config options.

        """
        for ext in extensions:
            if isinstance(ext, util.string_type):
                ext = self.build_extension(ext, configs.get(ext, {}))
            if isinstance(ext, Extension):
                ext.extendMarkdown(self, globals())
                logger.debug('Successfully loaded extension "%s.%s".',
                             ext.__class__.__module__, ext.__class__.__name__)
            elif ext is not None:
                raise TypeError('Extension "%s.%s" must be of type: "markdown.Extension"'
                                % (ext.__class__.__module__, ext.__class__.__name__))

        return self

    def build_extension(self, ext_name, configs):
        """Build extension by name, then return the module.

        The extension name may contain arguments as part of the string in the
        following format: "extname(key1=value1,key2=value2)"

        """

        configs = dict(configs)

        # Parse extensions config params (ignore the order)
        pos = ext_name.find("(")  # find the first "("
        if pos > 0:
            ext_args = ext_name[pos + 1:-1]
            ext_name = ext_name[:pos]
            pairs = [x.split("=") for x in ext_args.split(",")]
            configs.update([(x.strip(), y.strip()) for (x, y) in pairs])
            warnings.warn('Setting configs in the Named Extension string is '
                          'deprecated. It is recommended that you '
                          'pass an instance of the extension class to '
                          'Markdown or use the "extension_configs" keyword. '
                          'The current behavior will raise an error in version 2.7. '
                          'See the Release Notes for Python-Markdown version '
                          '2.6 for more info.', DeprecationWarning)

        # Get class name (if provided): `path.to.module:ClassName`
        ext_name, class_name = ext_name.split(':', 1) \
            if ':' in ext_name else (ext_name, '')

        # Try loading the extension first from one place, then another
        try:
            # Assume string uses dot syntax (`path.to.some.module`)
            module = importlib.import_module(ext_name)
            logger.debug('Successfuly imported extension module "%s".', ext_name)
            # For backward compat (until deprecation)
            # check that this is an extension.
            if ('.' not in ext_name and not
                    (hasattr(module, 'makeExtension') or
                     (class_name and hasattr(module, class_name)))):  # pragma: no cover
                # We have a name conflict
                # eg: extensions=['tables'] and PyTables is installed
                raise ImportError
        except ImportError:
            # Preppend `markdown.extensions.` to name
            module_name = '.'.join(['markdown.extensions', ext_name])
            try:
                module = importlib.import_module(module_name)
                logger.debug('Successfuly imported extension module "%s".', module_name)
                warnings.warn('Using short names for Markdown\'s builtin '
                              'extensions is deprecated. Use the '
                              'full path to the extension with Python\'s dot '
                              'notation (eg: "%s" instead of "%s"). The '
                              'current behavior will raise an error in version '
                              '2.7. See the Release Notes for '
                              'Python-Markdown version 2.6 for more info.' %
                              (module_name, ext_name),
                              DeprecationWarning)
            except ImportError:
                # Preppend `mdx_` to name
                module_name_old_style = '_'.join(['mdx', ext_name])
                try:
                    module = importlib.import_module(module_name_old_style)
                    logger.debug('Successfuly imported extension module "%s".', module_name_old_style)
                    warnings.warn('Markdown\'s behavior of prepending "mdx_" '
                                  'to an extension name is deprecated. '
                                  'Use the full path to the '
                                  'extension with Python\'s dot notation '
                                  '(eg: "%s" instead of "%s"). The current '
                                  'behavior will raise an error in version 2.7. '
                                  'See the Release Notes for Python-Markdown '
                                  'version 2.6 for more info.' %
                                  (module_name_old_style, ext_name),
                                  DeprecationWarning)
                except ImportError as e:
                    message = "Failed loading extension '%s' from '%s', '%s' " \
                              "or '%s'" % (ext_name, ext_name, module_name,
                                           module_name_old_style)
                    e.args = (message,) + e.args[1:]
                    raise

        if class_name:
            # Load given class name from module.
            return getattr(module, class_name)(**configs)
        else:
            # Expect  makeExtension() function to return a class.
            try:
                return module.makeExtension(**configs)
            except AttributeError as e:
                message = e.args[0]
                message = "Failed to initiate extension " \
                          "'%s': %s" % (ext_name, message)
                e.args = (message,) + e.args[1:]
                raise

    def registerExtension(self, extension):
        """ This gets called by the extension """
        self.registeredExtensions.append(extension)
        return self

    def reset(self):
        """
        Resets all state variables so that we can start with a new text.
        """
        self.htmlStash.reset()
        self.references.clear()
        self.metadata = {}

        for extension in self.registeredExtensions:
            if hasattr(extension, 'reset'):
                extension.reset()

        return self

    def convert(self, source):
        """
        Convert markdown to serialized XHTML or HTML.

        Keyword arguments:

        * source: Source text as a Unicode string.

        Markdown processing takes place in five steps:

        1. A bunch of "preprocessors" munge the input text.
        2. BlockParser() parses the high-level structural elements of the
           pre-processed text into an ElementTree.
        3. A bunch of "treeprocessors" are run against the ElementTree. One
           such treeprocessor runs InlinePatterns against the ElementTree,
           detecting inline markup.
        4. Some post-processors are run against the text after the ElementTree
           has been serialized into text.
        5. The output is written to a string.

        """

        # Fixup the source text
        if not source.strip():
            return ''  # a blank unicode string

        try:
            source = util.text_type(source)
        except UnicodeDecodeError as e:  # pragma: no cover
            # Customise error message while maintaining original trackback
            e.reason += '. -- Note: Markdown only accepts unicode input!'
            raise

        # Split into lines and run the line preprocessors.
        self.lines = source.split("\n")
        for prep in self.preprocessors.values():
            self.lines = prep.run(self.lines)

        # Parse the high-level elements.
        root = self.parser.parseDocument(self.lines).getroot()

        # Run the tree-processors
        for treeprocessor in self.treeprocessors.values():
            newRoot = treeprocessor.run(root)
            if newRoot is not None:
                root = newRoot

        # Serialize _properly_.  Strip top-level tags.
        output = self.serializer(root)
        if self.stripTopLevelTags:
            try:
                start = output.index('<%s>' % self.doc_tag) + len(self.doc_tag) + 2
                end = output.rindex('</%s>' % self.doc_tag)
                output = output[start:end].strip()
            except ValueError:  # pragma: no cover
                if output.strip().endswith('<%s />' % self.doc_tag):
                    # We have an empty document
                    output = ''
                else:
                    # We have a serious problem
                    raise ValueError('Markdown failed to strip top-level '
                                     'tags. Document=%r' % output.strip())

        # Run the text post-processors
        for pp in self.postprocessors.values():
            output = pp.run(output)

        return output.strip()

# EXPORTED FUNCTIONS
# =============================================================================
#
# Those are the only function we really mean to export: markdown()


def markdown(text, *args, **kwargs):
    """Convert a markdown string to HTML and return HTML as a unicode string.

    This is a shortcut function for `Markdown` class to cover the most
    basic use case.  It initializes an instance of Markdown, loads the
    necessary extensions and runs the parser on the given text.

    Keyword arguments:

    * text: Markdown formatted text as Unicode or ASCII string.
    * Any arguments accepted by the Markdown class.

    Returns: An HTML document as a string.

    """
    md = Markdown(*args, **kwargs)
    return md.convert(text)
