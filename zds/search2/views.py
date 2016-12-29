from elasticsearch_dsl import Search, Q

from django.conf import settings

from zds.search2.forms import SearchForm
from zds.search2.models import ESIndexManager
from zds.utils.paginator import ZdSPagingListView


class SearchView(ZdSPagingListView):
    template_name = 'search2/search.html'
    paginate_by = settings.ZDS_APP['search']['results_per_page']

    search_form_class = SearchForm
    search_query = None

    index_manager = None

    def __init__(self, **kwargs):
        super(SearchView, self).__init__(**kwargs)
        self.index_manager = ESIndexManager(settings.ES_INDEX_NAME)

    def get(self, request, *args, **kwargs):
        if 'q' in request.GET:
            self.search_query = ''.join(request.GET['q'])

        return super(SearchView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        if self.search_query:
            s = Search()

            queryset_topics = Q('match', _type='topic') & \
                Q('multi_match', query=self.search_query, fields=['title', 'subtitle', 'tags'])

            queryset_posts = Q('match', _type='post') & \
                Q('multi_match', query=self.search_query, fields=['text'])

            queryset_contents = Q('match', _type='publishedcontent') & \
                Q('multi_match', query=self.search_query, fields=['title', 'description', 'categories', 'tags', 'text'])

            queryset_chapters = Q('match', _type='chapter') & \
                Q('multi_match', query=self.search_query, fields=['title', 'text'])

            queryset = queryset_chapters | queryset_contents | queryset_topics | queryset_posts
            s = s.query(queryset)

            # .highlight_options(
            # order='score', fragment_size=250, number_of_fragments=2, pre_tags=['[hl]'], post_tags=['[/hl]'])
            #  s = s.highlight('title').highlight('text')

            return self.index_manager.setup_search(s)

        return []

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context['form'] = self.search_form_class(search_query=self.search_query, initial={})
        context['query'] = self.search_query is not None

        return context
