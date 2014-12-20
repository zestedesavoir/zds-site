# coding: utf-8

from django.shortcuts import render

from haystack.views import SearchView

from zds.search.constants import MODEL_NAMES
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
            'model_name': MODEL_NAMES
        }

        if self.results and hasattr(self.results, 'query') and self.results.query.backend.include_spelling:
            context['suggestion'] = self.form.get_suggestion()

        context.update(self.extra_context())
        return render(self.request, self.template, context)
