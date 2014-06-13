# coding: utf-8

from django.shortcuts import render_to_response
from haystack.views import SearchView
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
        }

        if self.results and hasattr(self.results, 'query') and self.results.query.backend.include_spelling:
            context['suggestion'] = self.form.get_suggestion()

        context.update(self.extra_context())
        return render_to_response(self.template, context, context_instance=self.context_class(self.request))