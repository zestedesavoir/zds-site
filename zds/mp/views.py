# coding: utf-8

from datetime import datetime
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
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
from zds.utils.mps import send_mp
from zds.utils.paginator import ZdSPagingListView
from zds.utils.templatetags.emarkdown import emarkdown
from .forms import PrivateTopicForm, PrivatePostForm
from .models import PrivateTopic, PrivatePost, \
    never_privateread, mark_read, PrivateTopicRead


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
        return PrivateTopic.objects \
            .filter(Q(participants__in=[self.request.user.id]) | Q(author=self.request.user.id)) \
            .select_related("author", "participants") \
            .distinct().order_by('-last_message__pubdate').all()


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


class PrivateTopicLeaveDetail(SingleObjectMixin, RedirectView):
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

        if topic.participants.count() == 0:
            topic.delete()
        elif request.user.pk == topic.author.pk:
            move = topic.participants.first()
            topic.author = move
            topic.participants.remove(move)
            topic.save()
        else:
            topic.participants.remove(request.user)
            topic.save()

        messages.success(request, _(u'Vous avez quitté la conversation avec succès.'))

        return redirect(reverse('mp-list'))


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


class PrivateTopicLeaveList(MultipleObjectMixin, RedirectView):
    """
    Leaves a list of MP.
    """

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(PrivateTopicLeaveList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        list = self.request.POST.getlist('items')
        return PrivateTopic.objects.filter(pk__in=list) \
            .filter(Q(participants__in=[self.request.user]) | Q(author=self.request.user))

    def post(self, request, *args, **kwargs):
        for topic in self.get_queryset():
            if topic.participants.all().count() == 0:
                topic.delete()
            elif request.user == topic.author:
                topic.author = topic.participants.all()[0]
                topic.participants.remove(topic.participants.all()[0])
                topic.save()
            else:
                topic.participants.remove(request.user)
                topic.save()
        return redirect(reverse('mp-list'))


class PrivatePostList(ZdSPagingListView, SingleObjectMixin):
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
        if never_privateread(self.object):
            mark_read(self.object)
        return context

    def get_queryset(self):
        return PrivatePost.objects \
            .filter(privatetopic__pk=self.object.pk) \
            .order_by('position_in_topic') \
            .all()


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
    def dispatch(self, request, *args, **kwargs):
        return super(PrivatePostAnswer, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        self.topic = super(PrivatePostAnswer, self).get_object(queryset)
        self.posts = PrivatePost.objects \
            .filter(privatetopic=self.topic) \
            .prefetch_related() \
            .order_by("-pubdate")[:settings.ZDS_APP['forum']['posts_per_page']]
        if not self.request.user == self.topic.author \
                and self.request.user not in list(self.topic.participants.all()):
            raise PermissionDenied
        return self.topic

    def get(self, request, *args, **kwargs):
        self.topic = self.get_object()
        text = ''

        # Using the quote button
        if 'cite' in request.GET:
            post_cite = get_object_or_404(PrivatePost, pk=(request.GET.get('cite')))

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
        post = PrivatePost()
        post.privatetopic = self.topic
        post.author = self.request.user
        post.text = form.data.get('text')
        post.text_html = emarkdown(form.data.get('text'))
        post.pubdate = datetime.now()
        post.position_in_topic = self.topic.get_post_count() + 1
        post.save()

        self.topic.last_message = post
        self.topic.save()

        # send email
        subject = u"{} - {} : {}".format(settings.ZDS_APP['site']['abbr'],
                                         _(u'Message Privé'),
                                         self.topic.title)
        from_email = u"{} <{}>".format(settings.ZDS_APP['site']['litteral_name'],
                                       settings.ZDS_APP['site']['email_noreply'])
        parts = list(self.topic.participants.all())
        parts.append(self.topic.author)
        parts.remove(self.request.user)
        for part in parts:
            profile = part.profile
            if profile.email_for_answer:
                pos = post.position_in_topic - 1
                last_read = PrivateTopicRead.objects.filter(
                    privatetopic=self.topic,
                    privatepost__position_in_topic=pos,
                    user=part).count()
                if last_read > 0:
                    context = {
                        'username': part.username,
                        'url': settings.ZDS_APP['site']['url'] + post.get_absolute_url(),
                        'author': self.request.user.username
                    }
                    message_html = render_to_string('email/mp/new.html', context)
                    message_txt = render_to_string('email/mp/new.txt', context)

                    msg = EmailMultiAlternatives(subject, message_txt, from_email, [part.email])
                    msg.attach_alternative(message_html, "text/html")
                    msg.send()

        return redirect(post.get_absolute_url())


class PrivatePostEdit(UpdateView):
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
        self.current_post.text = self.request.POST.get('text')
        self.current_post.text_html = emarkdown(self.request.POST.get('text'))
        self.current_post.update = datetime.now()
        self.current_post.save()

        return redirect(self.current_post.get_absolute_url())
