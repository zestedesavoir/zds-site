# coding: utf-8

import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import redirect, get_object_or_404, render, render_to_response
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import CreateView, RedirectView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin
from django.utils.translation import ugettext as _

from zds.member.models import Profile
from zds.mp.decorator import is_participant
from zds.mp.commons import LeavePrivateTopic, MarkPrivateTopicAsRead, UpdatePrivatePost
from zds.utils.mps import send_mp, send_message_mp
from zds.utils.paginator import ZdSPagingListView
from .forms import PrivateTopicForm, PrivatePostForm, PrivateTopicEditForm
from .models import PrivateTopic, PrivatePost


class PrivateTopicList(ZdSPagingListView):
    """
    Displays the list of private topics of a member given.
    """

    context_object_name = 'privatetopics'
    paginate_by = settings.ZDS_APP['forum']['topics_per_page']
    template_name = 'mp/index.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PrivateTopicList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return PrivateTopic.objects.get_private_topics_of_user(self.request.user.id)


class PrivateTopicNew(CreateView):
    """
    Creates a new MP.
    """

    form_class = PrivateTopicForm
    template_name = 'mp/topic/new.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PrivateTopicNew, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        title = request.GET.get('title') if 'title' in request.GET else None

        participants = None
        if 'username' in request.GET:
            dest_list = []
            # check that usernames in url is in the database
            for username in request.GET.getlist('username'):
                try:
                    dest_list.append(User.objects.get(username=username).username)
                except ObjectDoesNotExist:
                    pass
            if len(dest_list) > 0:
                participants = ', '.join(dest_list)

        form = self.form_class(username=request.user.username,
                               initial={
                                   'participants': participants,
                                   'title': title
                               })
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)

        if 'preview' in request.POST:
            if request.is_ajax():
                content = render_to_response('misc/previsualization.part.html', {'text': request.POST['text']})
                return StreamingHttpResponse(content)
            else:
                form = self.form_class(request.user.username,
                                       initial={
                                           'participants': request.POST['participants'],
                                           'title': request.POST['title'],
                                           'subtitle': request.POST['subtitle'],
                                           'text': request.POST['text'],
                                       })
        elif form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def get_form(self, form_class):
        return form_class(self.request.user.username, self.request.POST)

    def form_valid(self, form):
        participants = []
        for participant in form.data['participants'].split(","):
            current = participant.strip()
            if current == '':
                continue
            participants.append(get_object_or_404(User, username=current))

        p_topic = send_mp(self.request.user,
                          participants,
                          form.data['title'],
                          form.data['subtitle'],
                          form.data['text'],
                          True,
                          False)

        return redirect(p_topic.get_absolute_url())


class PrivateTopicEdit(UpdateView):
    """ Update mp informations """

    model = PrivateTopic
    template_name = "mp/topic/edit.html"
    form_class = PrivateTopicEditForm
    pk_url_kwarg = "pk"
    context_object_name = "topic"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PrivateTopicEdit, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        topic = super(PrivateTopicEdit, self).get_object(queryset)
        if topic is not None and not topic.author == self.request.user:
            raise PermissionDenied
        return topic


class PrivateTopicLeaveDetail(LeavePrivateTopic, SingleObjectMixin, RedirectView):
    """
    Leaves a MP.
    """
    queryset = PrivateTopic.objects.all()

    @method_decorator(login_required)
    @method_decorator(transaction.atomic)
    def dispatch(self, request, *args, **kwargs):
        return super(PrivateTopicLeaveDetail, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        topic = self.get_object()
        self.perform_destroy(topic)
        messages.success(request, _(u'Vous avez quitté la conversation avec succès.'))
        return redirect(reverse('mp-list'))

    def get_current_user(self):
        return self.request.user


class PrivateTopicAddParticipant(SingleObjectMixin, RedirectView):
    object = None
    queryset = PrivateTopic.objects.all()

    @method_decorator(login_required)
    @method_decorator(transaction.atomic)
    def dispatch(self, request, *args, **kwargs):
        return super(PrivateTopicAddParticipant, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        topic = super(PrivateTopicAddParticipant, self).get_object(self.queryset)
        if topic is not None and not topic.author == self.request.user:
            raise PermissionDenied
        return topic

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            participant = get_object_or_404(Profile, user__username=request.POST.get('username'))
            if participant.is_private():
                raise ObjectDoesNotExist
            if participant.user.pk == self.object.author.pk or participant.user in self.object.participants.all():
                messages.warning(request, _(u'Le membre que vous essayez d\'ajouter à la conversation y est déjà.'))
            else:
                self.object.participants.add(participant.user)
                self.object.save()
                # send email
                if participant.email_for_answer:
                    subject = u"{} - {} : {}".format(settings.ZDS_APP['site']['litteral_name'],
                                                     _(u'Message Privé'),
                                                     self.object.title)
                    from_email = u"{} <{}>".format(settings.ZDS_APP['site']['litteral_name'],
                                                   settings.ZDS_APP['site']['email_noreply'])
                    context = {
                        'username': participant.user.username,
                        'url': settings.ZDS_APP['site']['url'] + self.object.get_absolute_url(),
                        'author': request.user.username,
                        'site_name': settings.ZDS_APP['site']['litteral_name']
                    }
                    message_html = render_to_string('email/mp/new_participant.html', context)
                    message_txt = render_to_string('email/mp/new_participant.txt', context)

                    msg = EmailMultiAlternatives(subject, message_txt, from_email, [participant.user.email])
                    msg.attach_alternative(message_html, "text/html")
                    msg.send()
                messages.success(request, _(u'Le membre a bien été ajouté à la conversation.'))
        except Http404:
            messages.warning(request, _(u'Le membre que vous avez essayé d\'ajouter n\'existe pas.'))
        except ObjectDoesNotExist:
            messages.warning(request, _(u'Le membre que vous avez essayé d\'ajouter ne peut pas être contacté.'))

        return redirect(reverse('private-posts-list', args=[self.object.pk, self.object.slug()]))


class PrivateTopicLeaveList(LeavePrivateTopic, MultipleObjectMixin, RedirectView):
    """
    Leaves a list of MP.
    """

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(PrivateTopicLeaveList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        list = self.request.POST.getlist('items')
        return PrivateTopic.objects.get_private_topics_selected(self.request.user.id, list)

    def post(self, request, *args, **kwargs):
        for topic in self.get_queryset():
            self.perform_destroy(topic)
        return redirect(reverse('mp-list'))

    def get_current_user(self):
        return self.request.user


class PrivatePostList(MarkPrivateTopicAsRead, ZdSPagingListView, SingleObjectMixin):
    """
    Display a thread and its posts using a pager.
    """
    object = None
    paginate_by = settings.ZDS_APP['forum']['posts_per_page']
    template_name = 'mp/topic/index.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PrivatePostList, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=PrivateTopic.objects.all())
        if not self.object.author == request.user and request.user not in list(self.object.participants.all()):
            raise PermissionDenied
        return super(PrivatePostList, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PrivatePostList, self).get_context_data(**kwargs)
        context['topic'] = self.object
        context['last_post_pk'] = self.object.last_message.pk
        context['form'] = PrivatePostForm(self.object)
        context['posts'] = self.build_list_with_previous_item(context['object_list'])
        self.perform_list(self.object)
        return context

    def get_queryset(self):
        return PrivatePost.objects.get_message_of_a_private_topic(self.object.pk)


class PrivatePostAnswer(CreateView):
    """
    Creates a post to answer on a MP.
    """

    topic = None
    posts = None
    form_class = PrivatePostForm
    template_name = 'mp/post/new.html'
    queryset = PrivateTopic.objects.all()

    @method_decorator(login_required)
    @method_decorator(is_participant)
    def dispatch(self, request, *args, **kwargs):
        return super(PrivatePostAnswer, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        self.topic = super(PrivatePostAnswer, self).get_object(queryset)
        self.posts = PrivatePost.objects \
            .filter(privatetopic=self.topic) \
            .prefetch_related() \
            .order_by("-pubdate")[:settings.ZDS_APP['forum']['posts_per_page']]
        return self.topic

    def get(self, request, *args, **kwargs):
        self.topic = self.get_object()
        text = ''

        # Using the quote button
        if 'cite' in request.GET:
            try:
                post_cite = get_object_or_404(PrivatePost, pk=int(request.GET.get('cite')))
            except ValueError:
                raise Http404

            for line in post_cite.text.splitlines():
                text = text + '> ' + line + '\n'

            text = u'{0}Source:[{1}]({2}{3})'.format(
                text,
                post_cite.author.username,
                settings.ZDS_APP['site']['url'],
                post_cite.get_absolute_url())

            if request.is_ajax():
                resp = {}
                resp['text'] = text
                return HttpResponse(json.dumps(resp), content_type='application/json')

        form = self.form_class(self.topic, initial={
            'text': text
        })
        return render(request, self.template_name, {
            'topic': self.topic,
            'posts': self.posts,
            'last_post_pk': self.topic.last_message.pk,
            'form': form
        })

    def post(self, request, *args, **kwargs):
        self.topic = self.get_object()
        form = self.get_form(self.form_class)
        newpost = None
        if not request.is_ajax():
            newpost = self.topic.last_message.pk != int(request.POST.get('last_post'))

        if 'preview' in request.POST or newpost:
            if request.is_ajax():
                content = render_to_response('misc/previsualization.part.html', {'text': request.POST.get('text')})
                return StreamingHttpResponse(content)
            else:
                form = self.form_class(self.topic, initial={
                    'text': request.POST.get('text')
                })
        elif form.is_valid():
            return self.form_valid(form)

        return render(request, 'mp/post/new.html', {
            'topic': self.topic,
            'posts': self.posts,
            'last_post_pk': self.topic.last_message.pk,
            'newpost': newpost,
            'form': form,
        })

    def get_form(self, form_class):
        return form_class(self.topic, self.request.POST)

    def form_valid(self, form):
        send_message_mp(self.request.user, self.topic, form.data.get('text'), True, False)
        return redirect(self.topic.last_message.get_absolute_url())


class PrivatePostEdit(UpdateView, UpdatePrivatePost):
    """
    Edits a post on a MP.
    """

    current_post = None
    topic = None
    queryset = PrivatePost.objects.all()
    template_name = 'mp/post/edit.html'
    form_class = PrivatePostForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(PrivatePostEdit, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        # if post.position_in_topic >= 1:
        self.topic = get_object_or_404(PrivateTopic, pk=(self.kwargs.get('topic_pk', None)))
        self.current_post = super(PrivatePostEdit, self).get_object(queryset)
        last = get_object_or_404(PrivatePost, pk=self.topic.last_message.pk)
        # Only edit last private post
        if not last.pk == self.current_post.pk:
            raise PermissionDenied
        # Making sure the user is allowed to do that. Author of the post must to be the user logged.
        if self.current_post.author != self.request.user:
            raise PermissionDenied
        return self.current_post

    def get(self, request, *args, **kwargs):
        self.current_post = self.get_object()
        form = self.form_class(self.topic, initial={'text': self.current_post.text})
        form.helper.form_action = reverse('private-posts-edit',
                                          args=[self.topic.pk, self.topic.slug(), self.current_post.pk])
        return render(request, self.template_name, {
            'post': self.current_post,
            'topic': self.topic,
            'text': self.current_post.text,
            'form': form,
        })

    def post(self, request, *args, **kwargs):
        self.current_post = self.get_object()
        form = self.get_form(self.form_class)

        if 'preview' in request.POST:
            if request.is_ajax():
                content = render_to_response('misc/previsualization.part.html', {'text': request.POST['text']})
                return StreamingHttpResponse(content)
        elif form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {
            'post': self.current_post,
            'topic': self.topic,
            'form': form,
        })

    def get_form(self, form_class):
        form = self.form_class(self.topic, self.request.POST)
        form.helper.form_action = reverse('private-posts-edit',
                                          args=[self.topic.pk, self.topic.slug(), self.current_post.pk])
        return form

    def form_valid(self, form):
        self.perform_update(self.current_post, self.request.POST)

        return redirect(self.current_post.get_absolute_url())
