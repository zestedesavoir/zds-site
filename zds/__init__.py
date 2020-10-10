try:
    import ujson as json_handler
except ImportError:
    try:
        import simplejson as json_handler
    except ImportError:
        import json as json_handler
import logging

logging.debug("json is loaded, module is %s", json_handler.__name__)  # this allows to know which one we loaded
# and avoid pep8 warning.

# Try to load the version information from `zds/_version.py` and fallback to
# a default `dev` version.
#
# `zds/_version.py` should look like this:
#
#   __version__ = 'v27-foo'
#   git_version = '444c8f11acc921ef97c6971fc30bd91c383a3fea'
#
try:
    from ._version import __version__, git_version
except ImportError:
    __version__ = "dev"
    git_version = None
