from rest_framework_extensions.key_constructor.bits import QueryParamsKeyBit


class DJRF3xPaginationKeyBit(QueryParamsKeyBit):
    """
    A custom PaginationKeyBit for DJRF3

    This class solve an upstream issue:
        - Asking for page 1 and page 3 with a memcached instance will always return page 1.
    This issue have been discussed here: https://botbot.me/freenode/restframework/2015-05-23/?tz=Europe%2FLondon&page=1
    and in this Pull Request: https://github.com/zestedesavoir/zds-site/pull/2761

    This class should be deleted when an upstream solution will be proposed.
    This class should be replaced by using bits.PaginationKeyBit() instead.
    """
    def get_data(self, **kwargs):
        kwargs['params'] = []

        if hasattr(kwargs['view_instance'], 'paginator'):
            pqp = kwargs['view_instance'].paginator.page_query_param
            rqp = kwargs['view_instance'].request.query_params
            # add the query param
            kwargs['params'].append(pqp)
            # get its value
            rqp_pv = rqp.get(pqp, 1)
            kwargs['params'].append(rqp_pv)

        return super(DJRF3xPaginationKeyBit, self).get_data(**kwargs)
