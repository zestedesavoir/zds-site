# -*- coding: utf-8 -*-
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, RedirectView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from zds import settings
from zds.member.models import Profile
from zds.featured.forms import ResourceFeaturedForm, MessageFeaturedForm
from zds.featured.models import ResourceFeatured, MessageFeatured
from zds.utils.paginator import ZdSPagingListView


class ResourceFeaturedList(ZdSPagingListView):
    """
    Displays the list of featured.
    """

    context_object_name = 'featured_list'
    paginate_by = settings.ZDS_APP['featured']['featured_per_page']
    queryset = ResourceFeatured.objects.all()
    template_name = 'featured/index.html'

    @method_decorator(login_required)
    @method_decorator(permission_required('featured.change_resourcefeatured', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(ResourceFeaturedList, self).dispatch(request, *args, **kwargs)


class ResourceFeaturedCreate(CreateView):
    """
    Creates a new featured.
    """

    form_class = ResourceFeaturedForm
    template_name = 'featured/create.html'

    @method_decorator(login_required)
    @method_decorator(permission_required('featured.change_resourcefeatured', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(ResourceFeaturedCreate, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        featured = ResourceFeatured()
        featured.title = form.data.get('title')
        featured.type = form.data.get('type')
        featured.image_url = form.data.get('image_url')
        featured.url = form.data.get('url')
        featured.pubdate = datetime.now()
        featured.save()
        for author in form.data.get('authors').split(","):
            current = author.strip()
            if current == '':
                continue
            current_author = get_object_or_404(Profile, user__username=current)
            featured.authors.add(current_author)
        featured.save()

        return redirect(reverse('featured-list'))


class ResourceFeaturedUpdate(UpdateView):
    """
    Updates a featured
    """

    form_class = ResourceFeaturedForm
    template_name = 'featured/update.html'
    queryset = ResourceFeatured.objects.all()
    featured = None

    @method_decorator(login_required)
    @method_decorator(permission_required('featured.change_resourcefeatured', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(ResourceFeaturedUpdate, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.featured = self.get_object()
        form = self.form_class(initial={
            'title': self.featured.title,
            'type': self.featured.type,
            'image_url': self.featured.image_url,
            'url': self.featured.url,
            'authors': ", ".join([author.user.username for author in self.featured.authors.all()])
        })
        form.helper.form_action = reverse('featured-update', args=[self.featured.pk])
        return render(request, self.template_name, {'form': form, 'featured': self.featured})

    def post(self, request, *args, **kwargs):
        self.featured = self.get_object()
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form, 'featured': self.featured})

    def form_valid(self, form):
        self.featured.title = form.data.get('title')
        self.featured.type = form.data.get('type')
        self.featured.image_url = form.data.get('image_url')
        self.featured.url = form.data.get('url')
        self.featured.pubdate = datetime.now()
        self.featured.save()
        for author in form.data.get('authors').split(","):
            current = author.strip()
            if current == '':
                continue
            current_author = get_object_or_404(Profile, user__username=current)
            self.featured.authors.add(current_author)
        self.featured.save()

        return redirect(reverse('zds.pages.views.home'))

    def get_form(self, form_class):
        form = self.form_class(self.request.POST)
        form.helper.form_action = reverse('featured-update', args=[self.featured.pk])
        return form


class ResourceFeaturedDeleteDetail(SingleObjectMixin, RedirectView):
    """
    Deletes a featured
    """
    queryset = ResourceFeatured.objects.all()

    @method_decorator(login_required)
    @method_decorator(transaction.atomic)
    @method_decorator(permission_required('featured.change_resourcefeatured', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(ResourceFeaturedDeleteDetail, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        featured = self.get_object()
        featured.delete()

        messages.success(request, _(u'La une a été supprimée avec succès.'))

        return redirect(reverse('featured-list'))


class ResourceFeaturedDeleteList(MultipleObjectMixin, RedirectView):
    """
    Deletes a list of featured
    """

    @method_decorator(login_required)
    @method_decorator(permission_required('featured.change_resourcefeatured', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(ResourceFeaturedDeleteList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        list = self.request.POST.getlist('items')
        return ResourceFeatured.objects.filter(pk__in=list)

    def post(self, request, *args, **kwargs):
        for featured in self.get_queryset():
            featured.delete()

        messages.success(request, _(u'Les unes ont été supprimées avec succès.'))

        return redirect(reverse('featured-list'))


class MessageFeaturedCreateUpdate(CreateView):
    """
    Creates or updates the message featured.
    """

    form_class = MessageFeaturedForm
    template_name = 'featured/message/create.html'

    @method_decorator(login_required)
    @method_decorator(permission_required('featured.change_messagefeatured', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(MessageFeaturedCreateUpdate, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        last_message = MessageFeatured.objects.get_last_message()
        if last_message:
            last_message.delete()
        message_featured = MessageFeatured()
        message_featured.message = form.data.get('message')
        message_featured.url = form.data.get('url')
        message_featured.save()
        return redirect(reverse('zds.pages.views.home'))
