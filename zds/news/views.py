# -*- coding: utf-8 -*-
from datetime import datetime

from django.core.urlresolvers import reverse

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView

from zds import settings
from zds.member.models import Profile
from zds.news.forms import NewsForm
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


class NewsCreate(CreateView):
    """
    Creates a new news.
    """

    form_class = NewsForm
    template_name = 'news/create.html'

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        news = News()
        news.title = form.data.get('title')
        news.type = form.data.get('type')
        news.image_url = form.data.get('image_url')
        news.url = form.data.get('url')
        news.pubdate = datetime.now()
        news.save()
        for author in form.data.get('authors').split(","):
            current = author.strip()
            if current == '':
                continue
            current_author = get_object_or_404(Profile, user__username=current)
            print current_author
            news.authors.add(current_author)
        news.save()

        return redirect(reverse('zds.pages.views.home'))


class NewsUpdate(UpdateView):
    """
    Updates a news
    """

    form_class = NewsForm
    template_name = 'news/update.html'

    def get_object(self, queryset=None):
        return get_object_or_404(News, pk=(self.kwargs.get('news_pk', None)))

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        news = News()
        news.title = form.data.get('title')
        news.type = form.data.get('type')
        news.image_url = form.data.get('image_url')
        news.url = form.data.get('url')
        news.pubdate = datetime.now()
        news.save()
        for author in form.data.get('authors').split(","):
            current = author.strip()
            if current == '':
                continue
            current_author = get_object_or_404(Profile, user__username=current)
            print current_author
            news.authors.add(current_author)
        news.save()

        return redirect(reverse('zds.pages.views.home'))
