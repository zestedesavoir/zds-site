from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import redirect, get_object_or_404, render, render_to_response
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, RedirectView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from zds.member.models import Profile
from zds.mp.commons import LeavePrivateTopic, UpdatePrivatePost
from zds.mp.decorator import is_participant
from zds.utils.models import get_hat_from_request
from zds.utils.forums import CreatePostView
from zds.utils.mps import send_mp, send_message_mp
from zds.utils.paginator import ZdSPagingListView
from .forms import PrivateTopicForm, PrivatePostForm, PrivateTopicEditForm
from .models import PrivateTopic, PrivatePost, mark_read


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
                content = render_to_response('misc/preview.part.html', {'text': request.POST['text']})
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

    def get_form(self, form_class=PrivateTopicForm):
        return form_class(self.request.user.username, self.request.POST)

    def form_valid(self, form):
        participants = []
        for participant in form.data['participants'].split(','):
            current = participant.strip()
            if not current:
                continue
            participants.append(get_object_or_404(User, username=current))

        p_topic = send_mp(self.request.user,
                          participants,
                          form.data['title'],
                          form.data['subtitle'],
                          form.data['text'],
                          True,
                          False,
                          hat=get_hat_from_request(self.request))

        return redirect(p_topic.get_absolute_url())


class PrivateTopicEdit(UpdateView):
    """ Update mp informations """

    model = PrivateTopic
    template_name = 'mp/topic/edit.html'
    form_class = PrivateTopicEditForm
    pk_url_kwarg = 'pk'
    context_object_name = 'topic'

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
    permanent = True
    queryset = PrivateTopic.objects.all()

    @method_decorator(login_required)
    @method_decorator(transaction.atomic)
    def dispatch(self, request, *args, **kwargs):
        return super(PrivateTopicLeaveDetail, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        topic = self.get_object()
        self.perform_destroy(topic)
        messages.success(request, _('Vous avez quitté la conversation avec succès.'))
        return redirect(reverse('mp-list'))

    def get_current_user(self):
        return self.request.user


class PrivateTopicAddParticipant(SingleObjectMixin, RedirectView):
    permanent = True
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
                messages.warning(request, _('Le membre que vous essayez d\'ajouter à la conversation y est déjà.'))
            else:
                self.object.participants.add(participant.user)
                self.object.save()
                messages.success(request, _('Le membre a bien été ajouté à la conversation.'))
        except Http404:
            messages.warning(request, _('Le membre que vous avez essayé d\'ajouter n\'existe pas.'))
        except ObjectDoesNotExist:
            messages.warning(request, _('Le membre que vous avez essayé d\'ajouter ne peut pas être contacté.'))

        return redirect(reverse('private-posts-list', args=[self.object.pk, self.object.slug()]))


class PrivateTopicLeaveList(LeavePrivateTopic, MultipleObjectMixin, RedirectView):
    """
    Leaves a list of MP.
    """
    permanent = True

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
        mark_read(self.object, self.request.user)

        if self.object.last_message.author == self.request.user:
            context['user_can_modify'] = [self.object.last_message.pk]
        else:
            context['user_can_modify'] = []

        return context

    def get_queryset(self):
        return PrivatePost.objects.get_message_of_a_private_topic(self.object.pk)


class PrivatePostAnswer(CreatePostView):
    """
    Creates a post to answer on a MP.
    """

    model_quote = PrivatePost
    form_class = PrivatePostForm
    template_name = 'mp/post/new.html'
    queryset = PrivateTopic.objects.all()
    object = None
    posts = None

    @method_decorator(login_required)
    @method_decorator(is_participant)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.posts = PrivatePost.objects \
            .filter(privatetopic=self.object) \
            .prefetch_related() \
            .order_by('-pubdate')[:settings.ZDS_APP['forum']['posts_per_page']]
        return super(PrivatePostAnswer, self).dispatch(request, *args, **kwargs)

    def create_forum(self, form_class, **kwargs):
        return form_class(self.object, initial=kwargs)

    def get_form(self, form_class=PrivatePostForm):
        return form_class(self.object, self.request.POST)

    def form_valid(self, form):
        send_message_mp(self.request.user, self.object, form.data.get('text'), True, False,
                        hat=get_hat_from_request(self.request))
        return redirect(self.object.last_message.get_absolute_url())


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
                content = render_to_response('misc/preview.part.html', {'text': request.POST['text']})
                return StreamingHttpResponse(content)
        elif form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {
            'post': self.current_post,
            'topic': self.topic,
            'form': form,
        })

    def get_form(self, form_class=PrivatePostForm):
        form = self.form_class(self.topic, self.request.POST)
        form.helper.form_action = reverse('private-posts-edit',
                                          args=[self.topic.pk, self.topic.slug(), self.current_post.pk])
        return form

    def form_valid(self, form):
        self.perform_update(self.current_post, self.request.POST,
                            hat=get_hat_from_request(self.request, self.current_post.author))

        return redirect(self.current_post.get_absolute_url())
