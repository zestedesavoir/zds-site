# coding: utf-8

from haystack.views import SearchView

class CustomSearchView(SearchView):
    def extra_context(self):
        page_nbr = int(self.request.GET.get('page', 1))
        return {
            'nb': page_nbr
        }