#!/usr/bin/python
# -*- coding: utf-8 -*-
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import redirect, get_object_or_404, render, render_to_response
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from haystack.inputs import AutoQuery
from haystack.query import SearchQuerySet

from zds.forum.commons import TopicEditMixin, PostEditMixin, SinglePostObjectMixin
from zds.forum.forms import TopicForm, PostForm, MoveTopicForm
from zds.forum.models import Category, Forum, Topic, Post, never_read, mark_read, TopicRead
from zds.member.decorator import can_write_and_read_now
from zds.notification.models import TopicAnswerSubscription
from zds.utils import slugify
from zds.utils.forums import create_topic, send_post, CreatePostView
from zds.utils.mixins import FilterMixin
from zds.utils.models import Alert, Tag, CommentDislike, CommentLike
from zds.utils.mps import send_mp
from zds.utils.paginator import paginator_range, ZdSPagingListView


class CategoriesForumsListView(ListView):

    context_object_name = 'categories'
    template_name = 'forum/index.html'
    queryset = Category.objects.all()

    def get_context_data(self, **kwargs):
        context = super(CategoriesForumsListView, self).get_context_data(**kwargs)
        for category in context.get('categories'):
            category.forums = category.get_forums(self.request.user, with_count=True)
        return context


class CategoryForumsDetailView(DetailView):

    context_object_name = 'category'
    template_name = 'forum/category/index.html'
    queryset = Category.objects.all()

    def get_context_data(self, **kwargs):
        context = super(CategoryForumsDetailView, self).get_context_data(**kwargs)
        context['forums'] = context.get('category').get_forums(self.request.user)
        return context


class ForumTopicsListView(FilterMixin, ZdSPagingListView, SingleObjectMixin):

    context_object_name = 'topics'
    paginate_by = settings.ZDS_APP['forum']['topics_per_page']
    template_name = 'forum/category/forum.html'
    filter_url_kwarg = 'filter'
    default_filter_param = 'all'
    object = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_read(request.user):
            raise PermissionDenied
        return super(ForumTopicsListView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ForumTopicsListView, self).get_context_data(**kwargs)
        context['topics'] = list(context['topics'].all())
        sticky = list(
            self.filter_queryset(
                Topic.objects.get_all_topics_of_a_forum(self.object.pk, is_sticky=True),
                context['filter']))
        # we need to load it in memory because later we will get the
        # "already read topic" set out of this list and MySQL does not support that type of subquery
        context.update({
            'forum': self.object,
            'sticky_topics': sticky,
            'topic_read': TopicRead.objects.list_read_topic_pk(self.request.user, context['topics'] + sticky)
        })
        return context

    def get_object(self, queryset=None):
        forum = Forum.objects\
                     .select_related('category')\
                     .filter(slug=self.kwargs.get('forum_slug'))\
                     .first()
        if forum is None:
            raise Http404("Forum with slug {} was not found".format(self.kwargs.get('forum_slug')))
        return forum

    def get_queryset(self):
        self.queryset = Topic.objects.get_all_topics_of_a_forum(self.object.pk)
        return super(ForumTopicsListView, self).get_queryset()

    def filter_queryset(self, queryset, filter_param):
        if filter_param == 'solve':
            queryset = queryset.filter(is_solved=True)
        elif filter_param == 'unsolve':
            queryset = queryset.filter(is_solved=False)
        elif filter_param == 'noanswer':
            queryset = queryset.filter(last_message__position=1)
        return queryset


class TopicPostsListView(ZdSPagingListView, SingleObjectMixin):

    context_object_name = 'posts'
    paginate_by = settings.ZDS_APP['forum']['posts_per_page']
    template_name = 'forum/topic/index.html'
    object = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.forum.can_read(request.user):
            raise PermissionDenied
        if not self.kwargs.get('topic_slug') == slugify(self.object.title):
            return redirect(self.object.get_absolute_url())
        return super(TopicPostsListView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TopicPostsListView, self).get_context_data(**kwargs)
        form = PostForm(self.object, self.request.user)
        form.helper.form_action = reverse('post-new') + "?sujet=" + str(self.object.pk)

        context.update({
            'topic': self.object,
            'posts': self.build_list_with_previous_item(context['object_list']),
            'last_post_pk': self.object.last_message.pk,
            'form': form,
            'form_move': MoveTopicForm(topic=self.object),
        })
        reaction_ids = [post.pk for post in context['posts']]
        context["user_dislike"] = CommentDislike.objects\
            .select_related('comment')\
            .filter(user__pk=self.request.user.pk, comments__pk__in=reaction_ids)\
            .values_list('pk', flat=True)
        context["user_like"] = CommentLike.objects\
            .select_related('comment')\
            .filter(user__pk=self.request.user.pk, comments__pk__in=reaction_ids)\
            .values_list('pk', flat=True)
        context["is_staff"] = self.request.user.has_perm('forum.change_topic')
        if self.request.user.is_authenticated():
            if never_read(self.object):
                mark_read(self.object)
        return context

    def get_object(self, queryset=None):
        return get_object_or_404(Topic, pk=self.kwargs.get('topic_pk'))

    def get_queryset(self):
        return Post.objects.get_messages_of_a_topic(self.object.pk)


class TopicNew(CreateView, SingleObjectMixin):

    template_name = 'forum/topic/new.html'
    form_class = TopicForm
    object = None

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    @method_decorator(transaction.atomic)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_read(request.user):
            raise PermissionDenied
        return super(TopicNew, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        try:
            forum_pk = int(self.request.GET.get('forum'))
        except (KeyError, ValueError, TypeError):
            raise Http404
        return get_object_or_404(Forum, pk=forum_pk)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'forum': self.object, 'form': self.form_class()})

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)

        if "preview" in request.POST:
            if request.is_ajax():
                content = render_to_response('misc/previsualization.part.html', {'text': request.POST['text']})
                return StreamingHttpResponse(content)
            else:
                initial = {
                    "title": request.POST["title"],
                    "subtitle": request.POST["subtitle"],
                    "text": request.POST["text"]
                }
                form = self.form_class(initial=initial)
        elif form.is_valid():
            return self.form_valid(form)
        return render(request, self.template_name, {'forum': self.object, 'form': form})

    def get_form(self, form_class=TopicForm):
        return form_class(self.request.POST)

    def form_valid(self, form):
        topic = create_topic(
            self.request,
            self.request.user,
            self.object,
            form.data['title'],
            form.data['subtitle'],
            form.data['text'],
            None
        )
        return redirect(topic.get_absolute_url())


class TopicEdit(UpdateView, SingleObjectMixin, TopicEditMixin):

    template_name = 'forum/topic/edit.html'
    form_class = TopicForm
    object = None
    page = 1

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    @method_decorator(transaction.atomic)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.forum.can_read(request.user):
            return redirect(reverse('cats-forums-list'))
        if ('text' in request.POST or request.method == 'GET') \
                and self.object.author != request.user and not request.user.has_perm('forum.change_topic'):
            raise PermissionDenied
        if 'page' in request.POST:
            try:
                self.page = int(request.POST.get('page'))
            except (KeyError, ValueError, TypeError):
                self.page = 1
        return super(TopicEdit, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        is_staff = request.user.has_perm("forum.change_topic")
        if self.object.author != request.user and is_staff:
            messages.warning(request, _(
                u'Vous éditez un topic en tant que modérateur (auteur : {}). Soyez encore plus '
                u'prudent lors de l\'édition de celui-ci !').format(self.object.author.username))
        prefix = ''
        for tag in self.object.tags.all():
            prefix += u'[{0}]'.format(tag.title)

        form = self.create_form(self.form_class, **{
            'title': u'{0} {1}'.format(prefix, self.object.title).strip(),
            'subtitle': self.object.subtitle,
            'text': self.object.first_post().text
        })
        return render(request,
                      self.template_name,
                      {'topic': self.object, 'form': form, 'is_staff': is_staff})

    def post(self, request, *args, **kwargs):
        if 'text' in request.POST:
            form = self.get_form(self.form_class)

            if "preview" in request.POST:
                if request.is_ajax():
                    content = render_to_response('misc/previsualization.part.html', {'text': request.POST['text']})
                    return StreamingHttpResponse(content)
                else:
                    form = self.create_form(self.form_class, **{
                        'title': request.POST.get('title'),
                        'subtitle': request.POST.get('subtitle'),
                        'text': request.POST.get('text')
                    })
            elif form.is_valid():
                return self.form_valid(form)
            return render(request, self.template_name, {'topic': self.object, 'form': form})

        response = {}
        if 'follow' in request.POST:
            response['follow'] = self.perform_follow(self.object, request.user)
        elif 'email' in request.POST:
            response['email'] = self.perform_follow_by_email(self.object, request.user)
        elif 'solved' in request.POST:
            response['solved'] = self.perform_solve_or_unsolve(self.request.user, self.object)
        elif 'lock' in request.POST:
            self.perform_lock(self.object, request)
        elif 'sticky' in request.POST:
            self.perform_sticky(self.object, request)
        elif 'move' in request.POST:
            self.perform_move(request, self.object)

        self.object.save()
        if request.is_ajax():
            return HttpResponse(json.dumps(response), content_type='application/json')
        return redirect(u"{}?page={}".format(self.object.get_absolute_url(), self.page))

    def get_object(self, queryset=None):
        try:
            topic_pk = int(self.request.POST.get('topic'))
        except (KeyError, ValueError, TypeError):
            try:
                topic_pk = int(self.request.GET.get('topic'))
            except (KeyError, ValueError, TypeError):
                raise Http404
        return get_object_or_404(Topic, pk=topic_pk)

    def create_form(self, form_class, **kwargs):
        form = form_class(initial=kwargs)
        form.helper.form_action = reverse('topic-edit') + '?topic={}'.format(self.object.pk)
        return form

    def get_form(self, form_class=TopicForm):
        form = form_class(self.request.POST)
        form.helper.form_action = reverse('topic-edit') + '?topic={}'.format(self.object.pk)
        return form

    def form_valid(self, form):
        topic = self.perform_edit_info(self.object, self.request.POST, self.request.user)
        return redirect(topic.get_absolute_url())


class FindTopic(ZdSPagingListView, SingleObjectMixin):

    context_object_name = 'topics'
    template_name = 'forum/find/topic.html'
    paginate_by = settings.ZDS_APP['forum']['topics_per_page']
    pk_url_kwarg = 'user_pk'
    object = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(FindTopic, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(FindTopic, self).get_context_data(**kwargs)
        context.update({
            'usr': self.object
        })
        return context

    def get_queryset(self):
        return Topic.objects.get_all_topics_of_a_user(self.request.user, self.object)

    def get_object(self, queryset=None):
        return get_object_or_404(User, pk=self.kwargs.get(self.pk_url_kwarg))


class FindTopicByTag(FilterMixin, ZdSPagingListView, SingleObjectMixin):

    context_object_name = 'topics'
    paginate_by = settings.ZDS_APP['forum']['topics_per_page']
    template_name = 'forum/find/topic_by_tag.html'
    filter_url_kwarg = 'filter'
    default_filter_param = 'all'
    object = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(FindTopicByTag, self).get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(FindTopicByTag, self).get_context_data(*args, **kwargs)
        context['topics'] = list(context['topics'].all())
        # we need to load it in memory because later we will get the
        # "already read topic" set out of this list and MySQL does not support that type of subquery
        context.update({
            'tag': self.object,
            'topic_read': TopicRead.objects.list_read_topic_pk(self.request.user, context['topics'])
        })
        return context

    def get_object(self, queryset=None):
        return get_object_or_404(Tag, pk=self.kwargs.get('tag_pk'), slug=self.kwargs.get('tag_slug'))

    def get_queryset(self):
        self.queryset = Topic.objects.get_all_topics_of_a_tag(self.object, self.request.user)
        return super(FindTopicByTag, self).get_queryset()

    def filter_queryset(self, queryset, filter_param):
        if filter_param == 'solve':
            queryset = queryset.filter(is_solved=True)
        elif filter_param == 'unsolve':
            queryset = queryset.filter(is_solved=False)
        elif filter_param == 'noanswer':
            queryset = queryset.filter(last_message__position=1)
        return queryset


class PostNew(CreatePostView):

    model_quote = Post
    template_name = 'forum/post/new.html'
    form_class = PostForm
    object = None
    posts = None

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    @method_decorator(transaction.atomic)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.forum.can_read(request.user):
            raise PermissionDenied
        if self.object.is_locked:
            raise PermissionDenied
        if self.object.antispam(request.user):
            raise PermissionDenied
        self.posts = Post.objects.filter(topic=self.object) \
                         .prefetch_related() \
                         .order_by("-position")[:settings.ZDS_APP['forum']['posts_per_page']]
        return super(PostNew, self).dispatch(request, *args, **kwargs)

    def create_forum(self, form_class, **kwargs):
        form = form_class(self.object, self.request.user, initial=kwargs)
        form.helper.form_action = reverse('post-new') + "?sujet=" + str(self.object.pk)
        return form

    def get_form(self, form_class=PostForm):
        form = self.form_class(self.object, self.request.user, self.request.POST)
        form.helper.form_action = reverse('post-new') + "?sujet=" + str(self.object.pk)
        return form

    def form_valid(self, form):
        topic = send_post(self.request, self.object, self.request.user, form.data.get('text'))
        return redirect(topic.last_message.get_absolute_url())

    def get_object(self, queryset=None):
        try:
            topic_pk = int(self.request.GET.get('sujet'))
        except (KeyError, ValueError, TypeError):
            raise Http404
        return get_object_or_404(Topic, pk=topic_pk)


class PostEdit(UpdateView, SinglePostObjectMixin, PostEditMixin):

    template_name = 'forum/post/edit.html'
    form_class = PostForm

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    @method_decorator(transaction.atomic)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.topic.forum.can_read(request.user):
            raise PermissionDenied
        if self.object.author != request.user and not request.user.has_perm(
                'forum.change_post') and 'signal_message' not in request.POST:
            raise PermissionDenied
        return super(PostEdit, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.object.author != request.user and request.user.has_perm('forum.change_post'):
            messages.warning(request, _(
                u'Vous éditez ce message en tant que modérateur (auteur : {}). Soyez encore plus '
                u'prudent lors de l\'édition de celui-ci !').format(self.object.author.username))

        form = self.create_form(self.form_class, **{
            'text': self.object.text
        })
        return render(request, self.template_name, {
            'post': self.object,
            'topic': self.object.topic,
            'text': self.object.text,
            'form': form,
        })

    def post(self, request, *args, **kwargs):
        if 'text' in request.POST:
            form = self.get_form(self.form_class)

            if 'preview' in request.POST:
                if request.is_ajax():
                    content = render_to_response('misc/previsualization.part.html', {'text': request.POST.get('text')})
                    return StreamingHttpResponse(content)
                else:
                    form = self.create_form(self.form_class, **{
                        'text': request.POST.get('text')
                    })
            elif form.is_valid():
                return self.form_valid(form)
            return render(request, self.template_name, {
                'post': self.object,
                'topic': self.object.topic,
                'text': request.POST.get('text'),
                'form': form,
            })

        if 'delete_message' in request.POST:
            self.perform_hide_message(request, self.object, self.request.user, self.request.POST)
        if 'show_message' in request.POST:
            self.perform_show_message(self.object, self.request.user)
        if 'signal_message' in request.POST:
            self.perform_alert_message(request, self.object, request.user, request.POST.get('signal_text'))

        self.object.save()
        return redirect(self.object.get_absolute_url())

    def create_form(self, form_class, **kwargs):
        form = form_class(self.object.topic, self.request.user, initial=kwargs)
        form.helper.form_action = reverse('post-edit') + '?message=' + str(self.object.pk)
        return form

    def get_form(self, form_class=PostForm):
        form = self.form_class(self.object.topic, self.request.user, self.request.POST)
        form.helper.form_action = reverse('post-edit') + '?message=' + str(self.object.pk)
        return form

    def form_valid(self, form):
        post = self.perform_edit_post(self.object, self.request.user, self.request.POST.get('text'))
        return redirect(post.get_absolute_url())


class PostUseful(UpdateView, SinglePostObjectMixin, PostEditMixin):

    @method_decorator(require_POST)
    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.topic.forum.can_read(request.user):
            raise PermissionDenied
        if self.object.author == request.user or self.object.topic.author != request.user:
            if not request.user.has_perm("forum.change_post"):
                raise PermissionDenied
        return super(PostUseful, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.perform_useful(self.object)

        if request.is_ajax():
            return HttpResponse(json.dumps(self.object.is_useful), content_type='application/json')

        return redirect(self.object.get_absolute_url())


class PostUnread(UpdateView, SinglePostObjectMixin, PostEditMixin):

    @method_decorator(require_GET)
    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.topic.forum.can_read(request.user):
            raise PermissionDenied
        return super(PostUnread, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.perform_unread_message(self.object, self.request.user)

        return redirect(reverse("forum-topics-list", args=[
            self.object.topic.forum.category.slug, self.object.topic.forum.slug]))


class PostLike(UpdateView, SinglePostObjectMixin, PostEditMixin):

    @method_decorator(require_POST)
    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.topic.forum.can_read(request.user):
            raise PermissionDenied
        return super(PostLike, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.perform_like_post(self.object, self.request.user)

        if request.is_ajax():
            resp = {
                'upvotes': self.object.like,
                'downvotes': self.object.dislike
            }
            return HttpResponse(json.dumps(resp), content_type='application/json')
        return redirect(self.object.get_absolute_url())


class PostDisLike(PostLike):
    def post(self, request, *args, **kwargs):
        self.perform_dislike_post(self.object, self.request.user)

        if request.is_ajax():
            resp = {
                'upvotes': self.object.like,
                'downvotes': self.object.dislike
            }
            return HttpResponse(json.dumps(resp), content_type='application/json')
        return redirect(self.object.get_absolute_url())


class FindPost(FindTopic):

    context_object_name = 'posts'
    template_name = 'forum/find/post.html'
    paginate_by = settings.ZDS_APP['forum']['posts_per_page']

    def get_queryset(self):
        return Post.objects.get_all_messages_of_a_user(self.request.user, self.object)


@login_required
def followed_topics(request):
    """
    Displays the followed topics for the current user, with `settings.ZDS_APP['forum']['followed_topics_per_page']`
    topics per page.
    """
    topics_followed = TopicAnswerSubscription.objects.get_objects_followed_by(request.user)

    # Paginator

    paginator = Paginator(topics_followed, settings.ZDS_APP['forum']['followed_topics_per_page'])
    page = request.GET.get("page")
    try:
        shown_topics = paginator.page(page)
        page = int(page)
    except PageNotAnInteger:
        shown_topics = paginator.page(1)
        page = 1
    except EmptyPage:
        shown_topics = paginator.page(paginator.num_pages)
        page = paginator.num_pages
    topic_read = TopicRead.objects.list_read_topic_pk(request.user, shown_topics)
    return render(request, "forum/topic/followed.html",
                           {"followed_topics": shown_topics,
                            "topic_read": topic_read,
                            "pages": paginator_range(page,
                                                     paginator.num_pages),
                            "nb": page})


@can_write_and_read_now
@login_required
@require_POST
@transaction.atomic
def solve_alert(request):
    """
    Solves an alert (i.e. delete it from alert list) and sends an email to the user that created the alert, if the
    resolver leaves a comment.
    This can only be done by staff.
    """

    if not request.user.has_perm("forum.change_post"):
        raise PermissionDenied

    alert = get_object_or_404(Alert, pk=request.POST["alert_pk"])
    post = Post.objects.get(pk=alert.comment.id)

    if "text" in request.POST and request.POST["text"] != "":
        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        msg = render_to_string("forum/messages/solve_alert_pm.md", {
            'alert_author': alert.author.username,
            'post_author': post.author.username,
            'post_title': post.topic.title,
            'post_url': settings.ZDS_APP['site']['url'] + post.get_absolute_url(),
            'staff_name': request.user.username,
            'staff_message': request.POST["text"]
        })
        send_mp(
            bot,
            [alert.author],
            u"Résolution d'alerte : {0}".format(post.topic.title),
            "",
            msg,
            False,
        )

    alert.delete()
    messages.success(request, u"L'alerte a bien été résolue.")
    return redirect(post.get_absolute_url())


# TODO suggestions de recherche auto lors d'un nouveau topic, cf issues #99 et #580. Actuellement désactivées :(
def complete_topic(request):
    if not request.GET.get('q', None):
        return HttpResponse("{}", content_type='application/json')

    # TODO: WTF "sqs" ?!
    sqs = SearchQuerySet().filter(content=AutoQuery(request.GET.get('q'))).order_by('-pubdate').all()

    suggestions = {}

    cpt = 0
    for result in sqs:
        if cpt > 5:
            break
        if 'Topic' in str(result.model) and result.object.is_solved:
            suggestions[str(result.object.pk)] = (result.title, result.author, result.object.get_absolute_url())
            cpt += 1

    the_data = json.dumps(suggestions)

    return HttpResponse(the_data, content_type='application/json')
