# -*- coding: utf-8 -*-

from zds import settings
from zds.news.models import News

from zds.utils.paginator import ZdSPagingListView


class NewsList(ZdSPagingListView):
    """
    Displays the list of news.
    """

    context_object_name = 'news'
    paginate_by = settings.ZDS_APP['news']['news_per_page']
    queryset = News.objects.all()
    template_name = 'news/index.html'
