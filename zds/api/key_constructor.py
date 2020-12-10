"""
List of class to automatically create some obvious cache keys in API
"""

from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor

from zds.api.bits import DJRF3xPaginationKeyBit


class PagingListKeyConstructor(DefaultKeyConstructor):
    """Keys for a list api view"""

    pagination = DJRF3xPaginationKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()
    list_sql_query = bits.ListSqlQueryKeyBit()
    user = bits.UserKeyBit()


class DetailKeyConstructor(DefaultKeyConstructor):
    """Keys for a detail api view"""

    format = bits.FormatKeyBit()
    language = bits.LanguageKeyBit()
    retrieve_sql_query = bits.RetrieveSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()
    user = bits.UserKeyBit()
