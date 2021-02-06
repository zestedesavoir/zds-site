from rest_framework.pagination import PageNumberPagination

REST_PAGE_SIZE = 10
REST_PAGE_SIZE_QUERY_PARAM = "page_size"
REST_MAX_PAGE_SIZE = 100


class DefaultPagination(PageNumberPagination):
    page_size = REST_PAGE_SIZE
    page_size_query_param = REST_PAGE_SIZE_QUERY_PARAM
    max_page_size = REST_MAX_PAGE_SIZE
