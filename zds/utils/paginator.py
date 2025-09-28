from django.conf import settings
from django.core.paginator import EmptyPage, Paginator
from django.http import Http404
from django.views.generic import ListView
from django.views.generic.list import MultipleObjectMixin


class ZdSPagingListView(ListView):
    paginator = None
    page = 1

    def get_context_data(self, **kwargs):
        """
        Get the context for this view. This method is surcharged to modify the paginator
        and information given at the template.
        """
        queryset = kwargs.pop("object_list", self.object_list)
        page_size = self.get_paginate_by(queryset)
        context_object_name = self.get_context_object_name(queryset)
        self.paginator, self.page, queryset, is_paginated = self.paginate_queryset(queryset, page_size)
        if page_size:
            context = {
                "paginator": self.paginator,
                "page_obj": self.page,
                "is_paginated": is_paginated,
                "object_list": queryset,
                "pages": paginator_range(self.page.number, self.paginator.num_pages),
            }
        else:
            context = {
                "paginator": None,
                "page_obj": None,
                "is_paginated": False,
                "object_list": queryset,
                "pages": [],
            }
        if context_object_name is not None:
            context[context_object_name] = queryset
        context.update(kwargs)
        return super(MultipleObjectMixin, self).get_context_data(**context)

    def build_list_with_previous_item(self, queryset):
        """
        For some list paginated, we would like to display the last item of the previous page.
        This function returns the list paginated with this previous item.
        """
        original_list = queryset.all()
        items_list = []
        # If necessary, add the last item in the previous page.
        if self.page.number != 1:
            last_page = self.paginator.page(self.page.number - 1).object_list
            last_item = last_page[len(last_page) - 1]
            items_list.append(last_item)
        # Adds all items of the list paginated.
        for item in original_list:  # TODO: refacto
            items_list.append(item)
        return items_list


def paginator_range(current, stop, start=1):
    assert current <= stop

    # Basic case when no folding
    if stop - start <= settings.ZDS_APP["paginator"]["folding_limit"]:
        return list(range(start, stop + 1))

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


def make_pagination(
    context, request, queryset_objs, page_size, context_list_name="object_list", with_previous_item=False
):
    """This function will fill the context to use it for the paginator template, usefull if you cannot use
    `ZdSPagingListView`.

    Note that `/templates/misc/paginator.html` expect the following variables to be defined:

    - `paginator`: a valid `Paginator` object
    - `page_obj` : `QuerySet` object, portion of the `object_list`
    - `pages`: results from `paginator_range()`

    :param context: context
    :param request: page request
    :param queryset_objs: objects to paginate
    :param page_size: number of objects in a pages (last one from previous page not included!)
    :param context_list_name: control the name of the list object in the context
    :param with_previous_item: if `True`, will include the last object of the previous page to the list of shown objects
    """

    paginator = Paginator(queryset_objs, page_size)

    # retrieve page number
    if "page" in request.GET and request.GET["page"].isdigit():
        page_number = int(request.GET["page"])
    elif "page" not in request.GET:
        page_number = 1
    else:
        raise Http404
    try:
        page_obj = paginator.page(page_number)
    except EmptyPage:
        raise Http404

    page_objects_list = page_obj.object_list

    if page_number != 1 and with_previous_item:
        new_list = []
        last_page = paginator.page(page_obj.number - 1).object_list
        last_item = last_page[len(last_page) - 1]
        new_list.append(last_item)
        for item in page_objects_list:
            new_list.append(item)
        page_objects_list = new_list

    # fill context
    context["paginator"] = paginator
    context["page_obj"] = page_obj
    context["pages"] = paginator_range(page_number, paginator.num_pages)
    context[context_list_name] = page_objects_list
