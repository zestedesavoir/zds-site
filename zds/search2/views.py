# coding: utf-8
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Match, MultiMatch, FunctionScore, Term, Terms, Range

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from zds.search2.forms import SearchForm
from zds.search2.models import ESIndexManager
from zds.utils.paginator import ZdSPagingListView
from zds.forum.models import Forum


class SearchView(ZdSPagingListView):
    template_name = 'search2/search.html'
    paginate_by = settings.ZDS_APP['search']['results_per_page']

    search_form_class = SearchForm
    search_form = None
    search_query = None

    authorized_forums = ''

    index_manager = None

    def __init__(self, **kwargs):
        """Overridden because index manager must NOT be initialized elsewhere
        """

        super(SearchView, self).__init__(**kwargs)
        self.index_manager = ESIndexManager(settings.ES_INDEX_NAME)

    def get(self, request, *args, **kwargs):
        """Overridden to catch the request and fill the form.
        """

        if 'q' in request.GET:
            self.search_query = ''.join(request.GET['q'])

        self.search_form = self.search_form_class(data=self.request.GET, search_query=self.search_query)

        if self.search_query and not self.search_form.is_valid():
            raise PermissionDenied('research form is invalid')

        return super(SearchView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        if not self.index_manager.connected_to_es:
            messages.warning(self.request, _(u'Impossible de ce connecter à Elasticsearch'))
            return []

        if self.search_query:

            # find forums where the user is allowed to visit
            user = self.request.user

            forums_pub = Forum.objects.filter(group__isnull=True).all()
            if user and user.is_authenticated():
                forums_private = Forum \
                    .objects \
                    .filter(group__isnull=False, group__in=user.groups.all()).all()
                list_forums = list(forums_pub | forums_private)
            else:
                list_forums = list(forums_pub)

            self.authorized_forums = [f.pk for f in list_forums]

            search_queryset = Search()

            # setting the different querysets (according to the selected models, if any)
            part_querysets = []
            models = self.search_form.cleaned_data['models']

            if len(models) == 0:
                models = [p[0] for p in settings.ZDS_APP['search']['indexables']]

            for model in models:
                part_querysets.append(getattr(self, "get_queryset_{}s".format(model))())

            queryset = part_querysets[0]
            for query in part_querysets[1:]:
                queryset |= query

            # weighting:
            weight_functions = []
            for _type, weights in settings.ZDS_APP['search']['boosts'].items():
                if _type in models:
                    weight_functions.append({'filter': Match(_type=_type), 'weight': weights['global']})

            scored_queryset = FunctionScore(query=queryset, boost_mode='multiply', functions=weight_functions)
            search_queryset = search_queryset.query(scored_queryset)

            # highlighting:
            search_queryset = search_queryset.highlight_options(
                fragment_size=150, number_of_fragments=5, pre_tags=['[hl]'], post_tags=['[/hl]'])
            search_queryset = search_queryset.highlight('text').highlight('text_html')

            # executing:
            return self.index_manager.setup_search(search_queryset)

        return []

    def get_queryset_publishedcontents(self):
        """Find in PublishedContents.
        """

        query = Match(_type='publishedcontent') \
            & MultiMatch(query=self.search_query, fields=['title', 'description', 'categories', 'tags', 'text'])

        return query

    def get_queryset_chapters(self):
        """Find in chapters.
        """

        query = Match(_type='chapter') \
            & MultiMatch(query=self.search_query, fields=['title', 'text'])

        return query

    def get_queryset_topics(self):
        """Find in topics, and remove result if the forum is not allowed for the user.

        Score is modified if :

        + topic is solved ;
        + Topic is sticky ;
        + Topic is locked.

        """

        query = Match(_type='topic') \
            & Terms(forum_pk=self.authorized_forums) \
            & MultiMatch(query=self.search_query, fields=['title', 'subtitle', 'tags'])

        functions_score = [
            {'filter': Match(is_solved=True), 'weight': settings.ZDS_APP['search']['boosts']['topic']['if_solved']},
            {'filter': Match(is_sticky=True), 'weight': settings.ZDS_APP['search']['boosts']['topic']['if_sticky']},
            {'filter': Match(is_locked=True), 'weight': settings.ZDS_APP['search']['boosts']['topic']['if_locked']}
        ]

        scored_query = FunctionScore(query=query, boost_mode='multiply', functions=functions_score)

        return scored_query

    def get_queryset_posts(self):
        """Find in posts, and remove result if the forum is not allowed for the user or if the message is invisible.

        Score is modified if :

        + Post is the first one in a topic ;
        + Post is marked as "useful" ;
        + Post has a like/dislike ratio above (more like than dislike) or below (the other way around) 1.0.
        """

        query = Match(_type='post') \
            & Terms(forum_pk=self.authorized_forums) \
            & Term(is_visible=True) \
            & MultiMatch(query=self.search_query, fields=['text_html'])

        functions_score = [
            {'filter': Match(position=1), 'weight': settings.ZDS_APP['search']['boosts']['post']['if_first']},
            {'filter': Match(is_useful=True), 'weight': settings.ZDS_APP['search']['boosts']['post']['if_useful']},
            {
                'filter': Range(like_dislike_ratio={'gt': 1}),
                'weight': settings.ZDS_APP['search']['boosts']['post']['ld_ratio_above_1']
            },
            {
                'filter': Range(like_dislike_ratio={'lt': 1}),
                'weight': settings.ZDS_APP['search']['boosts']['post']['ld_ratio_below_1']
            }
        ]

        scored_query = FunctionScore(query=query, boost_mode='multiply', functions=functions_score)

        return scored_query

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context['form'] = self.search_form
        context['query'] = self.search_query is not None

        return context
