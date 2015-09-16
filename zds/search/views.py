# coding: utf-8
from django.db.models import Q

from django.shortcuts import render
from django.core.urlresolvers import reverse
from haystack.views import SearchView

from zds import settings
from zds.utils.paginator import paginator_range


class CustomSearchView(SearchView):

    def create_response(self):
        (paginator, page) = self.build_page()

        page_nbr = int(self.request.GET.get('page', 1))

        context = {
            'query': self.query,
            'form': self.form,
            'page': page,
            'pages': paginator_range(page_nbr, paginator.num_pages),
            'nb': page_nbr,
            'paginator': paginator,
            'suggestion': None,
            'model_name': '',
            'models': self.request.GET.getlist('models', ''),
        }

        if self.results and hasattr(self.results, 'query') and self.results.query.backend.include_spelling:
            context['suggestion'] = self.form.get_suggestion()

        context.update(self.extra_context())
        return render(self.request, self.template, context)

    def get_results(self):
        queryset = super(CustomSearchView, self).get_results()

        # We want to search only on authorized post and topic
        if self.request.user.is_authenticated():
            groups = self.request.user.groups

            if groups.count() > 0:
                return queryset.filter(Q(permissions="public") |
                                       Q(permissions__in=[group.name for group in groups.all()]))
            else:
                return queryset.filter(permissions="public")
        else:
            return queryset.filter(permissions="public")


def opensearch(request):
    """Generate OpenSearch Description file"""

    return render(request, 'search/opensearch.xml', {
        'site_name': settings.ZDS_APP['site']['litteral_name'],
        'site_url': settings.ZDS_APP['site']['url'],
        'language': settings.LANGUAGE_CODE,
        'search_url': settings.ZDS_APP['site']['url'] + reverse('haystack_search')
    }, content_type='application/opensearchdescription+xml')
