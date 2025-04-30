from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, RedirectView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from zds.forum.utils import CreatePostView
from zds.mp import signals
from zds.mp.commons import LeavePrivateTopic, UpdatePrivatePost
from zds.mp.decorator import is_participant
from zds.mp.utils import send_message_mp, send_mp
from zds.utils.misc import is_ajax
from zds.utils.models import get_hat_from_request
from zds.utils.paginator import ZdSPagingListView

from .forms import PrivatePostForm, PrivateTopicEditForm, PrivateTopicForm
from .models import PrivatePost, PrivatePostVote, PrivateTopic, PrivateTopicRead, is_reachable, mark_read


class PrivateTopicList(LoginRequiredMixin, ZdSPagingListView):
    """Display the list of private topics of a member."""

    context_object_name = "privatetopics"
    paginate_by = settings.ZDS_APP["forum"]["topics_per_page"]
    template_name = "mp/index.html"

    def get_queryset(self):
        return PrivateTopic.objects.get_private_topics_of_user(self.request.user.id)


class PrivateTopicNew(LoginRequiredMixin, CreateView):
    """Create a new private topic."""

    form_class = PrivateTopicForm
    template_name = "mp/topic/new.html"

    def get(self, request, *args, **kwargs):
        title = request.GET.get("title", "")

        usernames = request.GET.getlist("username", [])
        valid_usernames = User.objects.filter(username__in=usernames).values_list("username", flat=True)
        participants = ", ".join(valid_usernames)

        form = self.form_class(username=request.user.username, initial={"participants": participants, "title": title})

        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)

        if "preview" in request.POST:
            if is_ajax(request):
                content = render(request, "misc/preview.part.html", {"text": request.POST["text"]})
                return StreamingHttpResponse(content)
            else:
                form = self.form_class(
                    request.user.username,
                    initial={
                        "participants": request.POST["participants"],
                        "title": request.POST["title"],
                        "subtitle": request.POST["subtitle"],
                        "text": request.POST["text"],
                    },
                )
        elif form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {"form": form})

    def get_form(self, form_class=PrivateTopicForm):
        return form_class(self.request.user.username, self.request.POST)

    def form_valid(self, form):
        participants = []
        for participant in form.data["participants"].split(","):
            current = participant.strip()
            if not current:
                continue
            participants.append(get_object_or_404(User, username=current))

        p_topic = send_mp(
            self.request.user,
            participants,
            form.data["title"],
            form.data["subtitle"],
            form.data["text"],
            send_by_mail=True,
            leave=False,
            hat=get_hat_from_request(self.request),
        )

        return redirect(p_topic.get_absolute_url())


class PrivateTopicEdit(LoginRequiredMixin, UpdateView):
    """Edit a private topic."""

    model = PrivateTopic
    template_name = "mp/topic/edit.html"
    form_class = PrivateTopicEditForm
    context_object_name = "topic"

    def get_object(self, queryset=None):
        topic = super().get_object(queryset)
        if not topic.is_author(self.request.user):
            raise PermissionDenied
        return topic


class PrivateTopicLeaveDetail(LoginRequiredMixin, LeavePrivateTopic, SingleObjectMixin, RedirectView):
    """Leave a private topic."""

    permanent = True
    model = PrivateTopic

    @method_decorator(transaction.atomic)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        topic = self.get_object()
        if not topic.is_participant(self.get_current_user()):
            raise PermissionDenied
        self.perform_destroy(topic)
        messages.success(request, _("Vous avez quitté la conversation avec succès."))
        return redirect(reverse("mp:list"))

    def get_current_user(self):
        return self.request.user


class PrivateTopicAddParticipant(LoginRequiredMixin, SingleObjectMixin, RedirectView):
    """Add a participant to a private topic."""

    permanent = True
    model = PrivateTopic

    @method_decorator(transaction.atomic)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        topic = self.get_object()

        if not topic.is_author(self.request.user):
            raise PermissionDenied

        user = User.objects.filter(username=request.POST.get("username")).first()

        if user is None:
            messages.warning(request, _("Le membre n'a pas été ajouté à la conversation, car il n'existe pas."))
        elif not is_reachable(user):
            messages.warning(request, _("Le membre n'a pas été ajouté à la conversation, car il est injoignable."))
        elif topic.is_participant(user):
            messages.warning(request, _("Le membre n'a pas été ajouté à la conversation, car il y est déjà."))
        else:
            topic.add_participant(user)
            topic.save()
            messages.success(request, _("Le membre a bien été ajouté à la conversation."))

        return redirect(reverse("mp:view", args=[topic.pk, topic.slug()]))


class PrivateTopicLeaveList(LoginRequiredMixin, LeavePrivateTopic, MultipleObjectMixin, RedirectView):
    """Leave a list of private topics."""

    permanent = True

    def get_queryset(self):
        list = self.request.POST.getlist("items", [])
        return PrivateTopic.objects.get_private_topics_selected(self.request.user.id, list)

    def post(self, request, *args, **kwargs):
        for topic in self.get_queryset():
            self.perform_destroy(topic)
        return redirect(reverse("mp:list"))

    def get_current_user(self):
        return self.request.user


class PrivatePostList(LoginRequiredMixin, ZdSPagingListView, SingleObjectMixin):
    """Display a private topic and its posts using a pager."""

    paginate_by = settings.ZDS_APP["forum"]["posts_per_page"]
    template_name = "mp/topic/index.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=PrivateTopic.objects.all())
        if not self.object.is_participant(request.user):
            raise PermissionDenied
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["topic"] = self.object
        context["last_post_pk"] = self.object.last_message.pk
        context["form"] = PrivatePostForm(self.object)
        context["posts"] = self.build_list_with_previous_item(context["object_list"])
        mark_read(self.object, self.request.user)

        if self.object.last_message.author == self.request.user:
            context["user_can_modify"] = [self.object.last_message.pk]
        else:
            context["user_can_modify"] = []

        votes = PrivatePostVote.objects.filter(user_id=self.request.user.pk, private_post__in=context["posts"]).all()
        context["user_like"] = [vote.private_post_id for vote in votes if vote.positive]
        context["user_dislike"] = [vote.private_post_id for vote in votes if not vote.positive]

        return context

    def get_queryset(self):
        return PrivatePost.objects.get_message_of_a_private_topic(self.object.pk)


class PrivatePostAnswer(CreatePostView):
    """Create a post to answer in a private topic."""

    model_quote = PrivatePost
    form_class = PrivatePostForm
    template_name = "mp/post/new.html"
    model = PrivateTopic

    @method_decorator(login_required)
    # This checks that the user is a participant in the topic *and* avoids leaking posts from other private topics.
    # It is NOT equivalent to checking topic.is_participant(user) only.
    @method_decorator(is_participant)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.posts = (
            PrivatePost.objects.filter(privatetopic=self.object)
            .prefetch_related()
            .order_by("-pubdate")[: settings.ZDS_APP["forum"]["posts_per_page"]]
        )
        return super().dispatch(request, *args, **kwargs)

    def create_forum(self, form_class, **kwargs):
        return form_class(self.object, initial=kwargs)

    def get_form(self, form_class=PrivatePostForm):
        return form_class(self.object, self.request.POST)

    def form_valid(self, form):
        send_message_mp(
            self.request.user,
            self.object,
            form.data.get("text"),
            send_by_mail=True,
            force_email=False,
            hat=get_hat_from_request(self.request),
        )
        return redirect(self.object.last_message.get_absolute_url())


class PrivatePostEdit(LoginRequiredMixin, UpdateView, UpdatePrivatePost):
    """Edit a post in a private topic."""

    model = PrivatePost
    template_name = "mp/post/edit.html"
    form_class = PrivatePostForm

    def get_object(self, queryset=None):
        self.post = super().get_object(queryset)
        self.topic = self.post.privatetopic
        last_post = get_object_or_404(PrivatePost, pk=self.topic.last_message.pk)
        # Only edit last private post
        if not last_post.pk == self.post.pk:
            raise PermissionDenied
        # Making sure the user is allowed to do that. Author of the post must be the logged user.
        if self.post.author != self.request.user:
            raise PermissionDenied
        return self.post

    def get(self, request, *args, **kwargs):
        self.post = self.get_object()
        form = self.form_class(self.topic, initial={"text": self.post.text})
        form.helper.form_action = reverse("mp:post-edit", args=[self.post.pk])
        return render(
            request,
            self.template_name,
            {
                "post": self.post,
                "topic": self.topic,
                "text": self.post.text,
                "form": form,
            },
        )

    def post(self, request, *args, **kwargs):
        self.post = self.get_object()
        form = self.get_form(self.form_class)

        if "preview" in request.POST:
            if is_ajax(request):
                content = render(request, "misc/preview.part.html", {"text": request.POST["text"]})
                return StreamingHttpResponse(content)
        elif form.is_valid():
            return self.form_valid(form)

        return render(
            request,
            self.template_name,
            {
                "post": self.post,
                "topic": self.topic,
                "form": form,
            },
        )

    def get_form(self, form_class=PrivatePostForm):
        form = self.form_class(self.topic, self.request.POST)
        form.helper.form_action = reverse("mp:post-edit", args=[self.post.pk])
        return form

    def form_valid(self, form):
        self.perform_update(self.post, self.request.POST, hat=get_hat_from_request(self.request, self.post.author))
        return redirect(self.post.get_absolute_url())


class PrivatePostUnread(LoginRequiredMixin, UpdateView):
    """Mark a private post as not read."""

    http_method_names = ["get"]
    model = PrivatePost

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.privatetopic.is_participant(request.user):
            raise PermissionDenied
        self.perform_unread_private_post(self.object, self.request.user)
        return redirect(reverse("mp:list"))

    @staticmethod
    def perform_unread_private_post(post, user):
        """Mark the private post as unread."""
        previous_post = post.get_previous()
        topic_read = PrivateTopicRead.objects.filter(privatetopic=post.privatetopic, user=user).first()
        if topic_read is None and previous_post is not None:
            PrivateTopicRead(privatepost=previous_post, privatetopic=post.privatetopic, user=user).save()
        elif topic_read is not None and previous_post is not None:
            topic_read.privatepost = previous_post
            topic_read.save()
        elif topic_read is not None:
            topic_read.delete()

        signals.message_unread.send(sender=post.privatetopic.__class__, instance=post, user=user)
