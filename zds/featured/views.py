from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, RedirectView, UpdateView, FormView, DeleteView
from django.views.generic.list import MultipleObjectMixin

from django.conf import settings
from zds.featured.forms import FeaturedResourceForm, FeaturedMessageForm
from zds.featured.models import FeaturedResource, FeaturedMessage
from zds.forum.models import Topic
from zds.tutorialv2.models.database import PublishedContent
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
    context_object_name = 'featured_resource'
    initial_error_message = _('Le contenu est introuvable')
    displayed_content_type = {'TUTORIAL': _('Un tutoriel'),
                              'ARTICLE': _('Un article'),
                              'OPINION': _('Un billet'),
                              'TOPIC': _('Un sujet')}

    @method_decorator(login_required)
    @method_decorator(permission_required('featured.change_featuredresource', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(FeaturedResourceCreate, self).dispatch(request, *args, **kwargs)

    def get_initial_topic_data(self, topic_id):
        try:
            content = Topic.objects.get(pk=int(topic_id))
        except (Topic.DoesNotExist, ValueError):
            messages.error(self.request, self.initial_error_message)
            return {}
        return {'title': content.title,
                'type': self.displayed_content_type['TOPIC'],
                'authors': str(content.author),
                'url': self.request.build_absolute_uri(content.get_absolute_url())}

    def get_initial_content_data(self, content_id):
        try:
            content = PublishedContent.objects.get(content__pk=int(content_id))
        except (PublishedContent.DoesNotExist, ValueError):
            messages.error(self.request, self.initial_error_message)
            return {}
        displayed_authors = ', '.join([str(x) for x in content.authors.all()])
        if content.content.image:
            image_url = content.content.image.physical.url
        else:
            image_url = None
        return {'title': content.title(),
                'type': self.displayed_content_type[content.content_type],
                'authors': displayed_authors,
                'url': self.request.build_absolute_uri(content.content.get_absolute_url_online()),
                'image_url': image_url}

    def get_initial(self):
        initial = super(FeaturedResourceCreate, self).get_initial()
        content_type = self.request.GET.get('content_type', None)
        content_id = self.request.GET.get('content_id', None)
        if content_type == 'topic' and content_id:
            initial.update(**self.get_initial_topic_data(content_id))
        elif content_type == 'published_content' and content_id:
            initial.update(**self.get_initial_content_data(content_id))
        return initial

    def get_form_kwargs(self):
        kw = super(FeaturedResourceCreate, self).get_form_kwargs()
        kw['hide_major_update_field'] = True
        return kw

    def form_valid(self, form):
        featured_resource = FeaturedResource()
        featured_resource.title = form.cleaned_data.get('title')
        featured_resource.type = form.cleaned_data.get('type')
        featured_resource.authors = form.cleaned_data.get('authors')
        featured_resource.image_url = form.cleaned_data.get('image_url')
        featured_resource.url = form.cleaned_data.get('url')

        if form.cleaned_data.get('major_update', False):
            featured_resource.pubdate = datetime.now()
        else:
            featured_resource.pubdate = form.cleaned_data.get('pubdate')

        featured_resource.save()

        messages.success(self.request, _('La une a été créée.'))
        return redirect(reverse('featured-resource-list'))


class FeaturedResourceUpdate(UpdateView):
    """
    Updates a featured resource.
    """

    form_class = FeaturedResourceForm
    template_name = 'featured/resource/update.html'
    queryset = FeaturedResource.objects.all()
    context_object_name = 'featured_resource'

    @method_decorator(login_required)
    @method_decorator(permission_required('featured.change_featuredresource', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        return super(FeaturedResourceUpdate, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super(FeaturedResourceUpdate, self).get_initial()
        initial.update({
            'title': self.object.title,
            'type': self.object.type,
            'authors': self.object.authors,
            'image_url': self.object.image_url,
            'url': self.object.url,
            'pubdate': self.object.pubdate,
        })

        return initial

    def form_valid(self, form):

        self.object.title = form.cleaned_data.get('title')
        self.object.type = form.cleaned_data.get('type')
        self.object.authors = form.cleaned_data.get('authors')
        self.object.image_url = form.cleaned_data.get('image_url')
        self.object.url = form.cleaned_data.get('url')
        if form.cleaned_data.get('major_update', False):
            self.object.pubdate = datetime.now()
        else:
            self.object.pubdate = form.cleaned_data.get('pubdate')

        messages.success(self.request, _('La une a été mise à jour.'))
        self.success_url = reverse('featured-resource-list')
        return super(FeaturedResourceUpdate, self).form_valid(form)

    def get_form(self, form_class=None):
        form = super(FeaturedResourceUpdate, self).get_form(form_class)
        form.helper.form_action = reverse('featured-resource-update', args=[self.object.pk])
        return form


class FeaturedResourceDeleteDetail(DeleteView):
    """
    Deletes a featured resource.
    """

    model = FeaturedResource

    @method_decorator(login_required)
    @method_decorator(transaction.atomic)
    @method_decorator(permission_required('featured.change_featuredresource', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        self.success_url = reverse('featured-resource-list')
        return super(FeaturedResourceDeleteDetail, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        r = super(FeaturedResourceDeleteDetail, self).post(request, *args, **kwargs)
        messages.success(request, _('La une a été supprimée avec succès.'))
        return r


class FeaturedResourceDeleteList(MultipleObjectMixin, RedirectView):
    """
    Deletes a list of featured resources.
    """
    permanent = False

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

        messages.success(request, _('Les unes ont été supprimées avec succès.'))

        return redirect(reverse('featured-resource-list'))


class FeaturedMessageCreateUpdate(FormView):
    """
    Creates or updates the featured message.
    """

    form_class = FeaturedMessageForm
    template_name = 'featured/message/create.html'
    last_message = None

    @method_decorator(login_required)
    @method_decorator(permission_required('featured.change_featuredmessage', raise_exception=True))
    def dispatch(self, request, *args, **kwargs):
        self.last_message = FeaturedMessage.objects.get_last_message()
        return super(FeaturedMessageCreateUpdate, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        init = super(FeaturedMessageCreateUpdate, self).get_initial()

        if self.last_message is not None:
            init.update({
                'hook': self.last_message.hook,
                'message': self.last_message.message,
                'url': self.last_message.url,
            })

        return init

    def form_valid(self, form):
        if self.last_message:
            self.last_message.delete()

        featured_message = FeaturedMessage()
        featured_message.hook = form.data.get('hook')
        featured_message.message = form.data.get('message')
        featured_message.url = form.data.get('url')
        featured_message.save()

        messages.success(self.request, _('Le message a été changé'))
        return redirect(reverse('featured-resource-list'))
