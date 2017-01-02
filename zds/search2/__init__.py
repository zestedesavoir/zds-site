# coding: utf-8
from elasticsearch import TransportError
from elasticsearch_dsl.connections import connections

from django.conf import settings

DEFAULT_ES_CONNECTIONS = {
    'default': {
        'hosts': ['localhost:9200'],
    }
}

SEARCH_INDEX = getattr(settings, 'ES_SEARCH_INDEX', {'name': 'elastic', 'shards': 5, 'replicas': 1})
CONNECTIONS = getattr(settings, 'ES_CONNECTIONS', DEFAULT_ES_CONNECTIONS)


def setup_es_connections():
    """Create connection(s) to Elasticsearch from parameters defined in the settings.

    CONNECTIONS is a dict, where the keys are connection aliases and the values are parameters to the
    ``elasticsearch_dsl.connections.connection.create_connection()`` function (which are directly passed to an
    Elasticsearch object, see http://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch for the options).

    """

    try:
        for alias, params in CONNECTIONS.items():
            connections.create_connection(alias, **params)
    except TransportError:
        pass

setup_es_connections()
