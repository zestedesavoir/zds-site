# coding: utf-8
from django.db.models import Q
from django.http import Http404

from django.shortcuts import render
from django.core.urlresolvers import reverse
from haystack.generic_views import SearchView

from zds import settings
from zds.search.forms import CustomSearchForm
from zds.utils.paginator import paginator_range


class CustomSearchView(SearchView):
    template_name = 'search/search.html'
    form_class = CustomSearchForm

    def form_valid(self, form):
        self.queryset = form.search()
        context = self.get_context_data(**{
            self.form_name: form,
            'query': form.cleaned_data.get(self.search_field),
            'object_list': self.queryset,
            'models': self.request.GET.getlist('models', ''),
        })

        # Retrieve page number
        if "page" in self.request.GET and self.request.GET["page"].isdigit():
            page_number = int(self.request.GET["page"])
        elif "page" not in self.request.GET:
            page_number = 1
        else:
            raise Http404

        # Create pagination
        paginator = self.get_paginator(self.queryset, self.paginate_by, 0, False)

        if paginator.num_pages == 0:
            num_pages = 1
        else:
            num_pages = paginator.num_pages

        context['nb'] = page_number
        context['pages'] = paginator_range(page_number, num_pages)

        return self.render_to_response(context)

    def get_queryset(self):
        queryset = super(CustomSearchView, self).queryset

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
        'email_contact': settings.ZDS_APP['site']['email_contact'],
        'language': settings.LANGUAGE_CODE,
        'search_url': settings.ZDS_APP['site']['url'] + reverse('haystack_search')
    }, content_type='application/opensearchdescription+xml')
