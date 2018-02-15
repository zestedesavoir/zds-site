try:
    import ujson as json_handler
except ImportError:
    try:
        import simplejson as json_handler
    except ImportError:
        import json as json_handler
import logging
logging.debug('json is loaded, module is %s', json_handler.__name__)  # this allows to know which one we loaded
# and avoid pep8 warning.
