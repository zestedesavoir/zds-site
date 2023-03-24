from elasticsearch import TransportError
from elasticsearch_dsl.connections import connections

from django.conf import settings

DEFAULT_SEARCH_CONNECTIONS = {
    "default": {
        "hosts": ["localhost:9200"],
    }
}

CONNECTIONS = getattr(settings, "SEARCH_CONNECTIONS", DEFAULT_SEARCH_CONNECTIONS)
ENABLED = getattr(settings, "SEARCH_ENABLED", False)


def setup_connections():
    """Create connection(s) to Elasticsearch from parameters defined in the settings.

    CONNECTIONS is a dict, where the keys are connection aliases and the values are parameters to the
    ``elasticsearch_dsl.connections.connection.create_connection()`` function (which are directly passed to an
    Elasticsearch object, see http://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch for the options).

    """

    try:
        for alias, params in list(CONNECTIONS.items()):
            connections.create_connection(alias, **params)
    except TransportError:
        pass


if ENABLED:
    setup_connections()
