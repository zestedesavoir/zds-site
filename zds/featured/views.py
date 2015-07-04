# -*- coding: utf-8 -*-
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, RedirectView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from zds import settings
from zds.featured.forms import FeaturedResourceForm, FeaturedMessageForm
from zds.featured.models import FeaturedResource, FeaturedMessage
from zds.utils.paginator import ZdSPagingListView


class FeaturedResourceList(ZdSPagingListView):
    """
    Displays the list of featured resources.
    """

    context_object_name = 'featured_resource_list'
    paginate_by = settings.ZDS_APP['featured_resource']['featured_per_page']
    queryset = FeaturedResource.objects.all().order_by('-pubdate')
    template_name = 'featured/index.html'

    @method_decorator(login_required)
    @method_decorator(permission_required('featured.change_featuredresource', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(FeaturedResourceList, self).dispatch(request, *args, **kwargs)


class FeaturedResourceCreate(CreateView):
    """
    Creates a new featured resource.
    """

    form_class = FeaturedResourceForm
    template_name = 'featured/resource/create.html'

    @method_decorator(login_required)
    @method_decorator(permission_required('featured.change_featuredresource', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(FeaturedResourceCreate, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):

        featured_resource = FeaturedResource()
        featured_resource.title = form.data.get('title')
        featured_resource.type = form.data.get('type')
        featured_resource.authors = form.data.get('authors')
        featured_resource.image_url = form.data.get('image_url')
        featured_resource.url = form.data.get('url')
        featured_resource.pubdate = datetime.now()
        featured_resource.save()

        return redirect(reverse('featured-resource-list'))


class FeaturedResourceUpdate(UpdateView):
    """
    Updates a featured resource.
    """

    form_class = FeaturedResourceForm
    template_name = 'featured/resource/update.html'
    queryset = FeaturedResource.objects.all()
    featured_resource = None

    @method_decorator(login_required)
    @method_decorator(permission_required('featured.change_featuredresource', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(FeaturedResourceUpdate, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.featured_resource = self.get_object()
        form = self.form_class(initial={
            'title': self.featured_resource.title,
            'type': self.featured_resource.type,
            'authors': self.featured_resource.authors,
            'image_url': self.featured_resource.image_url,
            'url': self.featured_resource.url,
        })
        form.helper.form_action = reverse('featured-resource-update', args=[self.featured_resource.pk])
        return render(request, self.template_name, {'form': form, 'featured_resource': self.featured_resource})

    def post(self, request, *args, **kwargs):
        self.featured_resource = self.get_object()
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form, 'featured_resource': self.featured_resource})

    def form_valid(self, form):

        self.featured_resource.title = form.data.get('title')
        self.featured_resource.type = form.data.get('type')
        self.featured_resource.authors = form.data.get('authors')
        self.featured_resource.image_url = form.data.get('image_url')
        self.featured_resource.url = form.data.get('url')
        if form.data.get('major_update') is not None:
            self.featured_resource.pubdate = datetime.now()

        self.featured_resource.save()
        return redirect(reverse('zds.pages.views.home'))

    def get_form(self, form_class):
        form = self.form_class(self.request.POST)
        form.helper.form_action = reverse('featured-resource-update', args=[self.featured_resource.pk])
        return form


class FeaturedResourceDeleteDetail(SingleObjectMixin, RedirectView):
    """
    Deletes a featured resource.
    """
    queryset = FeaturedResource.objects.all()

    @method_decorator(login_required)
    @method_decorator(transaction.atomic)
    @method_decorator(permission_required('featured.change_featuredresource', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(FeaturedResourceDeleteDetail, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        featured_resource = self.get_object()
        featured_resource.delete()

        messages.success(request, _(u'La une a été supprimée avec succès.'))

        return redirect(reverse('featured-resource-list'))


class FeaturedResourceDeleteList(MultipleObjectMixin, RedirectView):
    """
    Deletes a list of featured resources.
    """

    @method_decorator(login_required)
    @method_decorator(permission_required('featured.change_featuredresource', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(FeaturedResourceDeleteList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        items_list = self.request.POST.getlist('items')
        return FeaturedResource.objects.filter(pk__in=items_list)

    def post(self, request, *args, **kwargs):
        for featured_resource in self.get_queryset():
            featured_resource.delete()

        messages.success(request, _(u'Les unes ont été supprimées avec succès.'))

        return redirect(reverse('featured-resource-list'))


class FeaturedMessageCreateUpdate(CreateView):
    """
    Creates or updates the featured message.
    """

    form_class = FeaturedMessageForm
    template_name = 'featured/message/create.html'

    @method_decorator(login_required)
    @method_decorator(permission_required('featured.change_featuredmessage', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(FeaturedMessageCreateUpdate, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        last_message = FeaturedMessage.objects.get_last_message()
        init = {}
        if last_message is not None:
            init = {
                'hook': last_message.hook,
                'message': last_message.message,
                'url': last_message.url,
            }

        form = self.form_class(initial=init)
        form.helper.form_action = reverse('featured-message-create')
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        last_message = FeaturedMessage.objects.get_last_message()
        if last_message:
            last_message.delete()
        featured_message = FeaturedMessage()
        featured_message.hook = form.data.get('hook')
        featured_message.message = form.data.get('message')
        featured_message.url = form.data.get('url')
        featured_message.save()
        return redirect(reverse('zds.pages.views.home'))
