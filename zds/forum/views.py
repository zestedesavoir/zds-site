import json

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from zds.featured.mixins import FeatureableMixin
from zds.forum import signals
from zds.forum.commons import ForumEditMixin, PostEditMixin, SinglePostObjectMixin, TopicEditMixin
from zds.forum.forms import MoveTopicForm, PostForm, TopicForm
from zds.forum.models import Forum, ForumCategory, Post, Topic, TopicRead, mark_read
from zds.forum.utils import CreatePostView, create_topic, send_post
from zds.member.decorator import can_write_and_read_now
from zds.member.models import user_readable_forums
from zds.notification.models import NewTopicSubscription, TopicAnswerSubscription
from zds.utils import old_slugify
from zds.utils.context_processor import get_repository_url
from zds.utils.misc import is_ajax
from zds.utils.mixins import FilterMixin
from zds.utils.models import Alert, CommentVote, Tag
from zds.utils.paginator import ZdSPagingListView


class CategoriesForumsListView(ListView):
    context_object_name = "categories"
    template_name = "forum/index.html"
    queryset = ForumCategory.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for category in context.get("categories"):
            category.forums = category.get_forums(self.request.user, with_count=True)
        return context


class ForumCategoryForumsDetailView(DetailView):
    context_object_name = "category"
    template_name = "forum/category/index.html"
    queryset = ForumCategory.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["forums"] = context.get("category").get_forums(self.request.user)
        return context


class LastTopicsListView(ListView):
    context_object_name = "topics"
    template_name = "forum/last_topics.html"

    def get_queryset(self):
        ordering = self.request.GET.get("order")
        if ordering not in ("creation", "last_post"):
            ordering = "creation"
        query_order = {"creation": "-pubdate", "last_post": "-last_message__pubdate"}.get(ordering)
        topics = (
            Topic.objects.select_related("forum")
            .filter(forum__in=user_readable_forums(self.request.user))
            .order_by(query_order)[: settings.ZDS_APP["forum"]["topics_per_page"]]
        )
        return topics

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({"topic_read": TopicRead.objects.list_read_topic_pk(self.request.user, context["topics"])})

        return context


class ForumTopicsListView(FilterMixin, ForumEditMixin, ZdSPagingListView, UpdateView, SingleObjectMixin):
    context_object_name = "topics"
    paginate_by = settings.ZDS_APP["forum"]["topics_per_page"]
    template_name = "forum/category/forum.html"
    fields = "__all__"
    filter_url_kwarg = "filter"
    default_filter_param = "all"
    object = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_read(request.user):
            raise PermissionDenied
        return super(ZdSPagingListView, self).get(request, *args, **kwargs)

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    @method_decorator(transaction.atomic)
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        response = {}
        if "follow" in request.POST:
            response["follow"] = self.perform_follow(self.object, request.user)
            response["subscriberCount"] = NewTopicSubscription.objects.get_subscriptions(self.object).count()
        elif "email" in request.POST:
            response["email"] = self.perform_follow_by_email(self.object, request.user)

        self.object.save()
        if is_ajax(request):
            return HttpResponse(json.dumps(response), content_type="application/json")
        return redirect(f"{self.object.get_absolute_url()}?page={self.page}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["topics"] = list(context["topics"].all())
        sticky = list(
            self.filter_queryset(
                Topic.objects.get_all_topics_of_a_forum(self.object.pk, is_sticky=True), context["filter"]
            )
        )
        # we need to load it in memory because later we will get the
        # "already read topic" set out of this list and MySQL does not support that type of subquery

        # Add a topic.is_followed attribute
        followed_queryset = TopicAnswerSubscription.objects.get_objects_followed_by(self.request.user.id)
        followed_topics = list(set(followed_queryset) & set(context["topics"] + sticky))
        for topic in set(context["topics"] + sticky):
            topic.is_followed = topic in followed_topics

        context.update(
            {
                "forum": self.object,
                "sticky_topics": sticky,
                "topic_read": TopicRead.objects.list_read_topic_pk(self.request.user, context["topics"] + sticky),
                "subscriber_count": NewTopicSubscription.objects.get_subscriptions(self.object).count(),
            }
        )
        return context

    def get_object(self, queryset=None):
        forum = (
            Forum.objects.prefetch_related("groups")
            .select_related("category")
            .filter(slug=self.kwargs.get("forum_slug"))
            .first()
        )
        if forum is None:
            raise Http404("Forum with slug {} was not found".format(self.kwargs.get("forum_slug")))
        return forum

    def get_queryset(self):
        self.queryset = Topic.objects.get_all_topics_of_a_forum(self.object.pk)
        return super().get_queryset()

    def filter_queryset(self, queryset, filter_param):
        if filter_param == "solve":
            queryset = queryset.filter(solved_by__isnull=False)
        elif filter_param == "unsolve":
            queryset = queryset.filter(solved_by__isnull=True)
        elif filter_param == "noanswer":
            queryset = queryset.filter(last_message__position=1)
        return queryset


class TopicPostsListView(ZdSPagingListView, FeatureableMixin, SingleObjectMixin):
    context_object_name = "posts"
    paginate_by = settings.ZDS_APP["forum"]["posts_per_page"]
    template_name = "forum/topic/index.html"
    object = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.forum.can_read(request.user):
            raise PermissionDenied
        if not self.kwargs.get("topic_slug") == old_slugify(self.object.title):
            return redirect(self.object.get_absolute_url())
        return super().get(request, *args, **kwargs)

    def featured_request_allowed(self):
        return not self.object.is_locked

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = PostForm(self.object, self.request.user)
        form.helper.form_action = reverse("forum:post-new") + "?sujet=" + str(self.object.pk)

        posts = self.build_list_with_previous_item(context["object_list"])
        context.update(
            {
                "topic": self.object,
                "posts": posts,
                "last_post_pk": self.object.last_message.pk,
                "form": form,
                "form_move": MoveTopicForm(topic=self.object),
            }
        )

        votes = CommentVote.objects.filter(user_id=self.request.user.pk, comment__in=context["posts"]).all()
        context["user_like"] = [vote.comment_id for vote in votes if vote.positive]
        context["user_dislike"] = [vote.comment_id for vote in votes if not vote.positive]
        context["is_staff"] = self.request.user.has_perm("forum.change_topic")
        context["is_antispam"] = self.object.antispam()
        context["subscriber_count"] = TopicAnswerSubscription.objects.get_subscriptions(self.object).count()
        if hasattr(self.request.user, "profile"):
            context["is_dev"] = self.request.user.profile.is_dev()
            context["has_token"] = self.request.user.profile.github_token != ""
            context["repositories"] = settings.ZDS_APP["github_projects"]["repositories"]

        if self.request.user.has_perm("forum.change_topic"):
            context["user_can_modify"] = [post.pk for post in context["posts"]]
        else:
            context["user_can_modify"] = [post.pk for post in context["posts"] if post.author == self.request.user]

        if self.request.user.is_authenticated:
            if len(posts) > 0:
                signals.post_read.send(sender=posts[0].__class__, instances=posts, user=self.request.user)
            if not self.object.is_read:
                mark_read(self.object)
        return context

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = Topic.objects
        result = (
            queryset.filter(pk=self.kwargs.get("topic_pk"))
            .select_related("solved_by", "author")
            .prefetch_related("tags")
            .first()
        )
        if result is None:
            raise Http404(f"Pas de forum avec l'identifiant {self.kwargs.get('topic_pk')}")
        return result

    def get_queryset(self):
        return Post.objects.get_messages_of_a_topic(self.object.pk)


class TopicNew(CreateView, SingleObjectMixin):
    template_name = "forum/topic/new.html"
    form_class = TopicForm
    object = None

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, request, *args, **kwargs):
        with transaction.atomic():
            self.object = self.get_object()
            if self.object.can_read(request.user):
                return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied

    def get_object(self, queryset=None):
        try:
            forum_pk = int(self.request.GET.get("forum"))
        except (KeyError, ValueError, TypeError):
            raise Http404
        return get_object_or_404(Forum, pk=forum_pk)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"forum": self.object, "form": self.form_class()})

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)

        if "preview" in request.POST:
            if is_ajax(request):
                content = render(request, "misc/preview.part.html", {"text": request.POST["text"]})
                return StreamingHttpResponse(content)
            else:
                initial = {
                    "title": request.POST["title"],
                    "subtitle": request.POST["subtitle"],
                    "text": request.POST["text"],
                }
                form = self.form_class(initial=initial)
        elif form.is_valid():
            return self.form_valid(form)
        return render(request, self.template_name, {"forum": self.object, "form": form})

    def get_form(self, form_class=TopicForm):
        return form_class(self.request.POST)

    def form_valid(self, form):
        topic = create_topic(
            self.request,
            self.request.user,
            self.object,
            form.data["title"],
            form.data["subtitle"],
            form.data["text"],
            tags=form.data["tags"],
        )
        return redirect(topic.get_absolute_url())


class TopicEdit(UpdateView, SingleObjectMixin, TopicEditMixin, FeatureableMixin):
    template_name = "forum/topic/edit.html"
    form_class = TopicForm
    object = None
    page = 1

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    @method_decorator(transaction.atomic)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.forum.can_read(request.user):
            return redirect(reverse("forum:cats-forums-list"))
        if (
            ("text" in request.POST or request.method == "GET")
            and self.object.author != request.user
            and not request.user.has_perm("forum.change_topic")
        ):
            raise PermissionDenied
        if (
            ("text" in request.POST or request.method == "GET")
            and not self.object.first_post().is_visible
            and not request.user.has_perm("forum.change_topic")
        ):
            raise PermissionDenied
        if "page" in request.POST:
            try:
                self.page = int(request.POST.get("page"))
            except (KeyError, ValueError, TypeError):
                self.page = 1
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        is_staff = request.user.has_perm("forum.change_topic")
        if self.object.author != request.user and is_staff:
            messages.warning(
                request,
                _(
                    "Vous éditez ce sujet en tant que modérateur (auteur : {}). Soyez encore plus "
                    "prudent lors de l'édition de celui-ci !"
                ).format(self.object.author.username),
            )
        form = self.create_form(
            self.form_class,
            **{
                "title": self.object.title,
                "subtitle": self.object.subtitle,
                "text": self.object.first_post().text,
                "tags": ", ".join(self.object.tags.values_list("title", flat=True)),
            },
        )
        return render(request, self.template_name, {"topic": self.object, "form": form, "is_staff": is_staff})

    def featured_request_allowed(self):
        return not self.object.is_locked

    def post(self, request, *args, **kwargs):
        if "text" in request.POST:
            form = self.get_form(self.form_class)

            if "preview" in request.POST:
                if is_ajax(request):
                    content = render(request, "misc/preview.part.html", {"text": request.POST["text"]})
                    return StreamingHttpResponse(content)
                else:
                    form = self.create_form(
                        self.form_class,
                        **{
                            "title": request.POST.get("title"),
                            "subtitle": request.POST.get("subtitle"),
                            "text": request.POST.get("text"),
                            "tags": request.POST.get("tags"),
                        },
                    )
            elif form.is_valid():
                return self.form_valid(form)
            return render(request, self.template_name, {"topic": self.object, "form": form})

        response = {}
        if "follow" in request.POST:
            response["follow"] = self.perform_follow(self.object, request.user).is_active
            response["subscriberCount"] = TopicAnswerSubscription.objects.get_subscriptions(self.object).count()
        elif "email" in request.POST:
            response["email"] = self.perform_follow_by_email(self.object, request.user).is_active
        elif "solved" in request.POST:
            response["solved"] = self.perform_solve_or_unsolve(self.request.user, self.object)
        elif "lock" in request.POST:
            self.perform_lock(request, self.object)
        elif "sticky" in request.POST:
            self.perform_sticky(request, self.object)
        elif "move" in request.POST:
            self.perform_move()
        elif "request_featured" in request.POST:
            response["requesting"], response["newCount"] = self.toogle_featured_request(request.user)

        self.object.save()
        if is_ajax(request):
            return HttpResponse(json.dumps(response), content_type="application/json")
        return redirect(f"{self.object.get_absolute_url()}?page={self.page}")

    def get_object(self, queryset=None):
        try:
            if "topic" in self.request.GET:
                topic_pk = int(self.request.GET["topic"])
            elif "topic" in self.request.POST:
                topic_pk = int(self.request.POST["topic"])
            else:
                raise Http404("Impossible de trouver votre sujet.")
        except (KeyError, ValueError, TypeError):
            raise Http404
        return get_object_or_404(Topic, pk=topic_pk)

    def create_form(self, form_class, **kwargs):
        form = form_class(initial=kwargs)
        form.helper.form_action = reverse("forum:topic-edit") + f"?topic={self.object.pk}"
        return form

    def get_form(self, form_class=TopicForm):
        form = form_class(self.request.POST)
        form.helper.form_action = reverse("forum:topic-edit") + f"?topic={self.object.pk}"
        return form

    def form_valid(self, form):
        topic = self.perform_edit_info(self.request, self.object, self.request.POST, self.request.user)
        return redirect(topic.get_absolute_url())


class FindTopic(ZdSPagingListView, SingleObjectMixin):
    context_object_name = "topics"
    template_name = "forum/find/topic.html"
    paginate_by = settings.ZDS_APP["forum"]["topics_per_page"]
    pk_url_kwarg = "user_pk"
    object = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "usr": self.object,
                "hidden_topics_count": Topic.objects.filter(author=self.object).count() - context["paginator"].count,
                "created_topics": True,
            }
        )
        return context

    def get_queryset(self):
        return Topic.objects.get_all_topics_of_a_user(self.request.user, self.object)

    def get_object(self, queryset=None):
        return get_object_or_404(User, pk=self.kwargs.get(self.pk_url_kwarg))


class FindFollowedTopic(ZdSPagingListView, SingleObjectMixin):
    context_object_name = "topics"
    template_name = "forum/find/topic.html"
    paginate_by = settings.ZDS_APP["forum"]["topics_per_page"]
    object = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        topics_count = self.object.profile.get_followed_topic_count()
        context.update(
            {
                "usr": self.object,
                "hidden_topics_count": topics_count - context["paginator"].count,
                "followed_topics": True,
            }
        )
        return context

    def get_queryset(self):
        return TopicAnswerSubscription.objects.get_objects_followed_by(self.request.user.id)

    def get_object(self, queryset=None):
        return get_object_or_404(User, pk=self.request.user.pk)


class FindTopicByTag(FilterMixin, ForumEditMixin, ZdSPagingListView, SingleObjectMixin):
    context_object_name = "topics"
    paginate_by = settings.ZDS_APP["forum"]["topics_per_page"]
    template_name = "forum/find/topic_by_tag.html"
    filter_url_kwarg = "filter"
    default_filter_param = "all"
    object = None

    def get(self, request, *args, **kwargs):
        if self.kwargs.get("tag_pk"):
            return redirect("forum:topic-tag-find", tag_slug=self.kwargs.get("tag_slug"), permanent=True)
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    @method_decorator(transaction.atomic)
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        response = {}
        if "follow" in request.POST:
            response["follow"] = self.perform_follow(self.object, request.user)
            response["subscriberCount"] = (NewTopicSubscription.objects.get_subscriptions(self.object).count(),)
        elif "email" in request.POST:
            response["email"] = self.perform_follow_by_email(self.object, request.user)

        self.object.save()
        if is_ajax(request):
            return HttpResponse(json.dumps(response), content_type="application/json")
        return redirect(f"{self.object.get_absolute_url()}?page={self.page}")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["topics"] = list(context["topics"].all())
        # we need to load it in memory because later we will get the
        # "already read topic" set out of this list and MySQL does not support that type of subquery
        context.update(
            {
                "tag": self.object,
                "subscriber_count": NewTopicSubscription.objects.get_subscriptions(self.object).count(),
                "topic_read": TopicRead.objects.list_read_topic_pk(self.request.user, context["topics"]),
            }
        )
        return context

    def get_object(self, queryset=None):
        return get_object_or_404(Tag, slug=self.kwargs.get("tag_slug"))

    def get_queryset(self):
        self.queryset = Topic.objects.get_all_topics_of_a_tag(self.object, self.request.user)
        return super().get_queryset()

    def filter_queryset(self, queryset, filter_param):
        if filter_param == "solve":
            queryset = queryset.filter(solved_by__isnull=False)
        elif filter_param == "unsolve":
            queryset = queryset.filter(solved_by__isnull=True)
        elif filter_param == "noanswer":
            queryset = queryset.filter(last_message__position=1)
        return queryset


class PostNew(CreatePostView):
    model_quote = Post
    template_name = "forum/post/new.html"
    form_class = PostForm
    object = None
    posts = None

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, request, *args, **kwargs):
        with transaction.atomic():
            self.object = self.get_object()
            can_read = self.object.forum.can_read(request.user)
            not_locked = not self.object.is_locked
            not_spamming = not self.object.antispam(request.user)
            if can_read and not_locked and not_spamming:
                self.posts = (
                    Post.objects.filter(topic=self.object)
                    .prefetch_related()
                    .order_by("-position")[: settings.ZDS_APP["forum"]["posts_per_page"]]
                )
                return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied

    def create_forum(self, form_class, **kwargs):
        form = form_class(self.object, self.request.user, initial=kwargs)
        form.helper.form_action = reverse("forum:post-new") + "?sujet=" + str(self.object.pk)
        return form

    def get_form(self, form_class=PostForm):
        form = self.form_class(self.object, self.request.user, self.request.POST)
        form.helper.form_action = reverse("forum:post-new") + "?sujet=" + str(self.object.pk)
        return form

    def form_valid(self, form):
        topic = send_post(self.request, self.object, self.request.user, form.data.get("text"))
        return redirect(topic.last_message.get_absolute_url())

    def get_object(self, queryset=None):
        try:
            topic_pk = int(self.request.GET.get("sujet"))
        except (KeyError, ValueError, TypeError):
            raise Http404
        return get_object_or_404(Topic, pk=topic_pk)


class PostEdit(UpdateView, SinglePostObjectMixin, PostEditMixin):
    template_name = "forum/post/edit.html"
    form_class = PostForm

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, request, *args, **kwargs):
        with transaction.atomic():
            self.object = self.get_object()
            is_author = self.object.author == request.user
            can_read = self.object.topic.forum.can_read(request.user)
            is_visible = self.object.is_visible
            if can_read and ((is_author and is_visible) or request.user.has_perm("forum.change_post")):
                return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied

    def get(self, request, *args, **kwargs):
        if self.object.author != request.user and request.user.has_perm("forum.change_post"):
            messages.warning(
                request,
                _(
                    "Vous éditez ce message en tant que modérateur (auteur : {}). Soyez encore plus "
                    "prudent lors de l'édition de celui-ci !"
                ).format(self.object.author.username),
            )

        form = self.create_form(self.form_class, **{"text": self.object.text})
        return render(
            request,
            self.template_name,
            {
                "post": self.object,
                "topic": self.object.topic,
                "text": self.object.text,
                "form": form,
            },
        )

    def post(self, request, *args, **kwargs):
        if "text" in request.POST:
            form = self.get_form(self.form_class)

            if "preview" in request.POST:
                if is_ajax(request):
                    content = render(request, "misc/preview.part.html", {"text": request.POST.get("text")})
                    return StreamingHttpResponse(content)
                else:
                    form = self.create_form(self.form_class, **{"text": request.POST.get("text")})
            elif form.is_valid():
                return self.form_valid(form)
            return render(
                request,
                self.template_name,
                {
                    "post": self.object,
                    "topic": self.object.topic,
                    "text": request.POST.get("text"),
                    "form": form,
                },
            )

        if "delete_message" in request.POST:
            self.perform_hide_message(request, self.object, self.request.user, self.request.POST)
        if "show_message" in request.POST:
            self.perform_show_message(self.request, self.object)
        if "signal_message" in request.POST:
            raise PermissionDenied("Not the good URL anymore!")

        self.object.save()
        return redirect(self.object.get_absolute_url())

    def create_form(self, form_class, **kwargs):
        form = form_class(self.object.topic, self.request.user, initial=kwargs)
        form.helper.form_action = reverse("forum:post-edit") + "?message=" + str(self.object.pk)
        return form

    def get_form(self, form_class=PostForm):
        form = self.form_class(self.object.topic, self.request.user, self.request.POST)
        form.helper.form_action = reverse("forum:post-edit") + "?message=" + str(self.object.pk)
        return form

    def form_valid(self, form):
        post = self.perform_edit_post(self.request, self.object, self.request.user, self.request.POST.get("text"))
        return redirect(post.get_absolute_url())


class PostSignal(UpdateView, SinglePostObjectMixin, PostEditMixin):
    http_method_names = ["post"]

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, request, *args, **kwargs):
        with transaction.atomic():
            self.object = self.get_object()
            can_read = self.object.topic.forum.can_read(request.user)
            if can_read:
                return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied

    def post(self, request, *args, **kwargs):
        if "signal_message" in request.POST:
            self.perform_alert_message(request, self.object, request.user, request.POST.get("signal_text"))
        else:
            raise Http404("no signal_message in POST")

        self.object.save()
        return redirect(self.object.get_absolute_url())


class PostUseful(UpdateView, SinglePostObjectMixin, PostEditMixin):
    @method_decorator(require_POST)
    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.topic.forum.can_read(request.user):
            raise PermissionDenied
        if self.object.topic.author != request.user:
            if not request.user.has_perm("forum.change_post"):
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.perform_useful(self.object)

        if is_ajax(request):
            return HttpResponse(json.dumps(self.object.is_useful), content_type="application/json")

        return redirect(self.object.get_absolute_url())


class PostUnread(UpdateView, SinglePostObjectMixin, PostEditMixin):
    @method_decorator(require_GET)
    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.topic.forum.can_read(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.perform_unread_message(self.object, self.request.user)

        return redirect(
            reverse("forum:topics-list", args=[self.object.topic.forum.category.slug, self.object.topic.forum.slug])
        )


class FindPost(ZdSPagingListView, SingleObjectMixin):
    context_object_name = "posts"
    template_name = "forum/find/post.html"
    paginate_by = settings.ZDS_APP["forum"]["posts_per_page"]
    pk_url_kwarg = "user_pk"
    object = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "usr": self.object,
                "hidden_posts_count": Post.objects.filter(author=self.object).distinct().count()
                - context["paginator"].count,
            }
        )

        return context

    def get_queryset(self):
        return Post.objects.get_all_messages_of_a_user(self.request.user, self.object)

    def get_object(self, queryset=None):
        return get_object_or_404(User, pk=self.kwargs.get(self.pk_url_kwarg))


@can_write_and_read_now
@login_required
@permission_required("forum.change_post", raise_exception=True)
@require_POST
@transaction.atomic
def solve_alert(request):
    """
    Solves an alert (i.e. delete it from alert list) and sends an email to the user that created the alert, if the
    resolver leaves a comment.
    This can only be done by staff.
    """

    alert = get_object_or_404(Alert, pk=request.POST["alert_pk"])
    post = Post.objects.get(pk=alert.comment.id)

    resolve_reason = ""
    msg_title = ""
    msg_content = ""
    if "text" in request.POST and request.POST["text"]:
        resolve_reason = request.POST["text"]
        msg_title = _("Résolution d'alerte : {0}").format(post.topic.title)
        msg_content = render_to_string(
            "forum/messages/solve_alert_pm.md",
            {
                "alert_author": alert.author.username,
                "post_author": post.author.username,
                "post_title": post.topic.title,
                "post_url": settings.ZDS_APP["site"]["url"] + post.get_absolute_url(),
                "staff_name": request.user.username,
                "staff_message": resolve_reason,
            },
        )

    alert.solve(request.user, resolve_reason, msg_title, msg_content)
    messages.success(request, _("L'alerte a bien été résolue."))
    return redirect(post.get_absolute_url())


class ManageGitHubIssue(UpdateView):
    queryset = Topic.objects.all()

    @method_decorator(require_POST)
    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.profile.is_dev():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if "unlink" in request.POST:
            self.object.github_issue = None
            self.object.save()

            messages.success(request, _("Le sujet a été dissocié de son ticket."))
        elif "link" in request.POST:
            try:
                self.object.github_issue = int(request.POST["issue"])
                if self.object.github_issue < 1:
                    raise ValueError
                self.object.github_repository_name = request.POST["repository"]
                if request.POST["repository"] not in settings.ZDS_APP["github_projects"]["repositories"]:
                    raise ValueError
                self.object.save()

                messages.success(request, _("Le ticket a bien été associé."))
            except (KeyError, ValueError, OverflowError):
                messages.error(request, _("Une erreur est survenue avec le numéro fourni."))
        else:  # create
            if not request.POST.get("title") or not request.POST.get("body"):
                messages.error(request, _("Le titre et le contenu sont obligatoires."))

            elif not request.user.profile.github_token:
                messages.error(request, _("Aucun token d'identification GitHub n'a été renseigné."))

            else:
                body = _("{}\n\nSujet : {}\n*Envoyé depuis {}*").format(
                    request.POST["body"],
                    settings.ZDS_APP["site"]["url"] + self.object.get_absolute_url(),
                    settings.ZDS_APP["site"]["literal_name"],
                )
                try:
                    response = requests.post(
                        get_repository_url(request.POST["repository"], "issues_api"),
                        timeout=10,
                        headers={"Authorization": f"Token {self.request.user.profile.github_token}"},
                        json={"title": request.POST["title"], "body": body},
                    )
                    if response.status_code != 201:
                        raise Exception

                    json_response = response.json()
                    self.object.github_issue = json_response["number"]
                    self.object.github_repository_name = request.POST["repository"]
                    self.object.save()

                    messages.success(request, _("Le ticket a bien été créé."))
                except Exception:
                    messages.error(request, _("Un problème est survenu lors de l'envoi sur GitHub."))

        return redirect(self.object.get_absolute_url())
