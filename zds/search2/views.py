from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Match, MultiMatch, FunctionScore

from django.conf import settings
from django.core.exceptions import PermissionDenied

from zds.search2.forms import SearchForm
from zds.search2.models import ESIndexManager
from zds.utils.paginator import ZdSPagingListView


class SearchView(ZdSPagingListView):
    template_name = 'search2/search.html'
    paginate_by = settings.ZDS_APP['search']['results_per_page']

    search_form_class = SearchForm
    search_form = None
    search_query = None

    index_manager = None

    def __init__(self, **kwargs):
        super(SearchView, self).__init__(**kwargs)
        self.index_manager = ESIndexManager(settings.ES_INDEX_NAME)

    def get(self, request, *args, **kwargs):
        if 'q' in request.GET:
            self.search_query = ''.join(request.GET['q'])

        self.search_form = self.search_form_class(data=self.request.GET, search_query=self.search_query)

        if not self.search_form.is_valid():
            raise PermissionDenied('research form is invalid')

        return super(SearchView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        if self.search_query:
            search_queryset = Search()

            # setting the different querysets (according to the selected models if any)
            part_querysets = []
            models = self.search_form.cleaned_data['models']

            if len(models) == 0:
                part_querysets = [
                    self.get_queryset_chapters(),
                    self.get_queryset_publishedcontents(),
                    self.get_queryset_posts(),
                    self.get_queryset_topics()]
            else:
                for model in models:
                    if model == 'topic':
                        part_querysets.append(self.get_queryset_topics())
                    elif model == 'post':
                        part_querysets.append(self.get_queryset_posts())
                    elif model == 'chapter':
                        part_querysets.append(self.get_queryset_chapters())
                    elif model == 'publishedcontent':
                        part_querysets.append(self.get_queryset_publishedcontents())

            queryset = part_querysets[0]
            for query in part_querysets[1:]:
                queryset |= query

            # weighting:
            weights = []
            for _type, weight in settings.ZDS_APP['search']['boosts'].items():
                weights.append({'filter': Match(_type=_type), 'weight': weight})

            scored_queryset = FunctionScore(query=queryset, boost_mode='multiply', functions=weights)

            # executing:
            search_queryset = search_queryset.query(scored_queryset)

            # .highlight_options(
            # order='score', fragment_size=250, number_of_fragments=2, pre_tags=['[hl]'], post_tags=['[/hl]'])
            #  s = s.highlight('title').highlight('text')

            return self.index_manager.setup_search(search_queryset)

        return []

    def get_queryset_publishedcontents(self):
        query = Match(_type='publishedcontent') & \
            MultiMatch(query=self.search_query, fields=['title', 'description', 'categories', 'tags', 'text'])

        return query

    def get_queryset_chapters(self):
        query = Match(_type='chapter') & MultiMatch(query=self.search_query, fields=['title', 'text'])

        return query

    def get_queryset_topics(self):
        query = Match(_type='topic') & MultiMatch(query=self.search_query, fields=['title', 'subtitle', 'tags'])

        return query

    def get_queryset_posts(self):
        query = Match(_type='post') & MultiMatch(query=self.search_query, fields=['text'])

        return query

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context['form'] = self.search_form
        context['query'] = self.search_query is not None

        return context
