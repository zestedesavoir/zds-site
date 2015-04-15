# coding: utf-8

from django.views.generic import ListView
from django.views.generic.list import MultipleObjectMixin

from zds.settings import ZDS_APP


class ZdSPagingListView(ListView):
    paginator = None
    page = 1
    query_paginated = None

    def get_context_data(self, **kwargs):
        """
        Get the context for this view. This method is surcharged to modify the paginator
        and information given at the template.
        """
        queryset = kwargs.pop('object_list', self.object_list)
        page_size = self.get_paginate_by(queryset)
        context_object_name = self.get_context_object_name(queryset)
        self.paginator, self.page, self.query_paginated, is_paginated = self.paginate_queryset(queryset, page_size)
        if page_size:
            context = {
                'paginator': self.paginator,
                'page_obj': self.page,
                'is_paginated': is_paginated,
                'object_list': self.query_paginated,
                'pages': paginator_range(self.page.number, self.paginator.num_pages),
            }
        else:
            context = {
                'paginator': None,
                'page_obj': None,
                'is_paginated': False,
                'object_list': self.query_paginated,
                'pages': [],
            }
        if context_object_name is not None:
            context[context_object_name] = self.query_paginated
        context.update(kwargs)
        return super(MultipleObjectMixin, self).get_context_data(**context)

    def build_list(self):
        """
        For some list paginated, we would like to display the last item of the previous page.
        This function returns the list paginated with this previous item.
        """
        list = []
        # If necessary, add the last item in the previous page.
        if self.page.number != 1:
            last_page = self.paginator.page(self.page.number - 1).object_list
            last_item = (last_page)[len(last_page) - 1]
            list.append(last_item)
        # Adds all items of the list paginated.
        for item in self.query_paginated:
            list.append(item)
        return list


def paginator_range(current, stop, start=1):
    assert (current <= stop)

    # Basic case when no folding
    if stop - start <= ZDS_APP['paginator']['folding_limit']:
        return range(start, stop + 1)

    # Complex case when folding
    lst = []
    for page_number in range(start, stop + 1):
        # Bounds
        if page_number == start or page_number == stop:
            lst.append(page_number)
            if page_number == start and current - start > 2:
                lst.append(None)
        # Neighbors
        elif abs(page_number - current) == 1:
            lst.append(page_number)
            if page_number - current > 0 and stop - page_number > 2:
                lst.append(None)
        # Current
        elif page_number == current:
            lst.append(page_number)
        # Put some
        elif page_number == stop - 1 and current == stop - 3:
            lst.append(page_number)
            # And ignore all other numbers

    return lst
