from zds import json_handler
import operator

from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Match, MultiMatch, FunctionScore, Term, Terms, Range

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.views.generic import CreateView
from django.views.generic.detail import SingleObjectMixin

from zds.searchv2.forms import SearchForm
from zds.searchv2.models import ESIndexManager
from zds.utils.paginator import ZdSPagingListView
from zds.utils.templatetags.authorized_forums import get_authorized_forums
from functools import reduce


class SimilarTopicsView(CreateView, SingleObjectMixin):
    search_query = None
    authorized_forums = ''
    index_manager = None

    def __init__(self, **kwargs):
        """Overridden because the index manager must NOT be initialized elsewhere."""

        super(SimilarTopicsView, self).__init__(**kwargs)
        self.index_manager = ESIndexManager(**settings.ES_SEARCH_INDEX)

    def get(self, request, *args, **kwargs):
        if 'q' in request.GET:
            self.search_query = ''.join(request.GET['q'])

        results = []
        if self.index_manager.connected_to_es and self.search_query:
            self.authorized_forums = get_authorized_forums(self.request.user)

            search_queryset = Search()
            query = Match(_type='topic') \
                & Terms(forum_pk=self.authorized_forums) \
                & MultiMatch(query=self.search_query, fields=['title', 'subtitle', 'tags'])

            functions_score = [
                {'filter': Match(is_solved=True), 'weight': settings.ZDS_APP['search']['boosts']['topic']['if_solved']},
                {'filter': Match(is_sticky=True), 'weight': settings.ZDS_APP['search']['boosts']['topic']['if_sticky']},
                {'filter': Match(is_locked=True), 'weight': settings.ZDS_APP['search']['boosts']['topic']['if_locked']}
            ]

            scored_query = FunctionScore(query=query, boost_mode='multiply', functions=functions_score)
            search_queryset = search_queryset.query(scored_query)[:10]

            # Build the result
            for hit in search_queryset.execute():
                result = {'id': hit.pk,
                          'url': str(hit.get_absolute_url),
                          'title': str(hit.title),
                          'subtitle': str(hit.subtitle),
                          'forumTitle': str(hit.forum_title),
                          'forumUrl': str(hit.forum_get_absolute_url),
                          'pubdate': str(hit.pubdate),
                          }
                results.append(result)

        data = {'results': results}
        return HttpResponse(json_handler.dumps(data), content_type='application/json')


class SearchView(ZdSPagingListView):
    """Search view."""

    template_name = 'searchv2/search.html'
    paginate_by = settings.ZDS_APP['search']['results_per_page']

    search_form_class = SearchForm
    search_form = None
    search_query = None
    content_category = None
    content_subcategory = None

    authorized_forums = ''

    index_manager = None

    def __init__(self, **kwargs):
        """Overridden because the index manager must NOT be initialized elsewhere."""

        super(SearchView, self).__init__(**kwargs)
        self.index_manager = ESIndexManager(**settings.ES_SEARCH_INDEX)

    def get(self, request, *args, **kwargs):
        """Overridden to catch the request and fill the form."""

        if 'q' in request.GET:
            self.search_query = ''.join(request.GET['q'])

        self.search_form = self.search_form_class(data=self.request.GET)

        if self.search_query and not self.search_form.is_valid():
            raise PermissionDenied('research form is invalid')

        return super(SearchView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        if not self.index_manager.connected_to_es:
            messages.warning(self.request, _('Impossible de se connecter à Elasticsearch'))
            return []

        if self.search_query:

            # Searches forums the user is allowed to visit
            self.authorized_forums = get_authorized_forums(self.request.user)

            search_queryset = Search()

            # Restrict (sub)category if any
            if self.search_form.cleaned_data['category']:
                self.content_category = self.search_form.cleaned_data['category']
            if self.search_form.cleaned_data['subcategory']:
                self.content_subcategory = self.search_form.cleaned_data['subcategory']

            # Mark that contents must come from library if required
            self.from_library = False
            if self.search_form.cleaned_data['from_library'] == 'on':
                self.from_library = True

            # Setting the different querysets (according to the selected models, if any)
            part_querysets = []
            chosen_groups = self.search_form.cleaned_data['models']

            if chosen_groups:
                models = []
                for group in chosen_groups:
                    if group in settings.ZDS_APP['search']['search_groups']:
                        models.append(settings.ZDS_APP['search']['search_groups'][group][1])
            else:
                models = [v[1] for k, v in settings.ZDS_APP['search']['search_groups'].items()]

            models = reduce(operator.concat, models)

            for model in models:
                part_querysets.append(getattr(self, 'get_queryset_{}s'.format(model))())

            queryset = part_querysets[0]
            for query in part_querysets[1:]:
                queryset |= query

            # Weighting:
            weight_functions = []
            for _type, weights in list(settings.ZDS_APP['search']['boosts'].items()):
                if _type in models:
                    weight_functions.append({'filter': Match(_type=_type), 'weight': weights['global']})

            scored_queryset = FunctionScore(query=queryset, boost_mode='multiply', functions=weight_functions)
            search_queryset = search_queryset.query(scored_queryset)

            # Highlighting:
            search_queryset = search_queryset.highlight_options(
                fragment_size=150, number_of_fragments=5, pre_tags=['[hl]'], post_tags=['[/hl]'])
            search_queryset = search_queryset.highlight('text').highlight('text_html')

            # Executing:
            return self.index_manager.setup_search(search_queryset)

        return []

    def get_queryset_publishedcontents(self):
        """Search in PublishedContent objects."""

        query = Match(_type='publishedcontent') \
            & MultiMatch(
            query=self.search_query,
            fields=['title', 'description', 'categories', 'subcategories', 'tags', 'text'])

        if self.from_library:
            query &= Match(content_type='TUTORIAL') | Match(content_type='ARTICLE')

        if self.content_category:
            query &= Match(categories=self.content_category)

        if self.content_subcategory:
            query &= Match(subcategories=self.content_subcategory)

        functions_score = [
            {
                'filter': Match(content_type='TUTORIAL'),
                'weight': settings.ZDS_APP['search']['boosts']['publishedcontent']['if_tutorial']
            },
            {
                'filter': Match(content_type='TUTORIAL') & Match(has_chapters=True),
                'weight': settings.ZDS_APP['search']['boosts']['publishedcontent']['if_medium_or_big_tutorial']
            },
            {
                'filter': Match(content_type='ARTICLE'),
                'weight': settings.ZDS_APP['search']['boosts']['publishedcontent']['if_article']
            },
            {
                'filter': Match(content_type='OPINION'),
                'weight': settings.ZDS_APP['search']['boosts']['publishedcontent']['if_opinion']
            },
            {
                'filter': Match(content_type='OPINION') & Match(picked=False),
                'weight': settings.ZDS_APP['search']['boosts']['publishedcontent']['if_opinion_not_picked']
            },
        ]

        scored_query = FunctionScore(query=query, boost_mode='multiply', functions=functions_score)

        return scored_query

    def get_queryset_chapters(self):
        """Search in content chapters."""

        query = Match(_type='chapter') \
            & MultiMatch(query=self.search_query, fields=['title', 'text'])

        if self.content_category:
            query &= Match(categories=self.content_category)

        if self.content_subcategory:
            query &= Match(subcategories=self.content_subcategory)

        return query

    def get_queryset_topics(self):
        """Search in topics, and remove the result if the forum is not allowed for the user.

        Score is modified if:

        + topic is solved;
        + topic is sticky;
        + topic is locked.
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
        """Search in posts, and remove result if the forum is not allowed for the user or if the message is invisible.

        Score is modified if:

        + post is the first one in a topic;
        + post is marked as "useful";
        + post has a like/dislike ratio above (has more likes than dislikes) or below (the other way around) 1.0.
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


def opensearch(request):
    """Generate OpenSearch Description file."""

    return render(request, 'searchv2/opensearch.xml', {
        'site_name': settings.ZDS_APP['site']['literal_name'],
        'site_url': settings.ZDS_APP['site']['url'],
        'email_contact': settings.ZDS_APP['site']['email_contact'],
        'language': settings.LANGUAGE_CODE,
        'search_url': settings.ZDS_APP['site']['url'] + reverse('search:query')
    }, content_type='application/opensearchdescription+xml')
