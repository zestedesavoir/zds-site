import random
import sys
from datetime import datetime

import django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from zds.featured.models import FeaturedMessage, FeaturedResource
from zds.forum.models import Topic
from zds.member.decorator import can_write_and_read_now
from zds.pages.models import GroupContact
from zds.search.forms import SearchForm
from zds.tutorialv2.models.database import PublishableContent, PublishedContent
from zds.utils.context_processor import get_repository_url
from zds.utils.models import Alert, Comment, CommentEdit

try:
    with (settings.BASE_DIR / "quotes.txt").open("r", encoding="utf-8") as quotes_file:
        QUOTES = quotes_file.readlines()
except OSError:
    QUOTES = [settings.ZDS_APP["site"]["slogan"]]


def home(request):
    """Display the home page with last topics added."""

    tutos = PublishableContent.objects.get_last_tutorials()
    articles = PublishableContent.objects.get_last_articles()
    opinions = PublishableContent.objects.get_last_opinions()
    quote = random.choice(QUOTES)

    return render(
        request,
        "home.html",
        {
            "featured_message": FeaturedMessage.objects.get_last_message(),
            "last_tutorials": tutos,
            "last_articles": articles,
            "last_opinions": opinions,
            "last_featured_resources": FeaturedResource.objects.get_last_featured(),
            "last_topics": Topic.objects.get_last_topics(),
            "contents_count": PublishedContent.objects.get_contents_count(),
            "quote": quote.replace("\n", ""),
            "search_form": SearchForm(initial={}),
        },
    )


def index(request):
    return render(request, "pages/index.html")


def about(request):
    """Display many informations about the website."""
    return render(
        request,
        "pages/technologies.html",
        {
            "default_repository_url": get_repository_url(
                settings.ZDS_APP["github_projects"]["default_repository"], "base_url"
            ),
            "django_major_version": django.VERSION[0],
            "python_major_version": sys.version_info.major,
        },
    )


def association(request):
    """Display association's presentation."""
    return render(request, "pages/association.html")


def accessibility(request):
    """Display accessibility page"""
    return render(request, "pages/accessibility.html")


class ContactView(ListView):
    """
    Display contact page.
    """

    model = GroupContact
    queryset = GroupContact.objects.prefetch_related("persons_in_charge__profile", "group__user_set__profile").order_by(
        "position"
    )
    template_name = "pages/contact.html"
    context_object_name = "groups"


def eula(request):
    """End-User Licence Agreement."""
    return render(request, "pages/eula.html")


def cookies(request):
    """Cookies explanation page."""
    return render(request, "pages/cookies.html")


@can_write_and_read_now
@login_required
@permission_required("forum.change_post", raise_exception=True)
def alerts(request):
    outstanding = Alert.objects.filter(solved=False).order_by("-pubdate")
    solved = Alert.objects.filter(solved=True).order_by("-solved_date")[:15]

    return render(
        request,
        "pages/alerts.html",
        {
            "alerts": outstanding,
            "solved": solved,
        },
    )


class CommentEditsHistory(ListView):
    model = CommentEdit
    context_object_name = "edits"
    template_name = "pages/comment_edits_history.html"

    def get_object(self):
        return get_object_or_404(Comment, pk=self.kwargs["comment_pk"])

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        response = super().dispatch(*args, **kwargs)
        current_user = self.request.user
        if not self.get_object().author == current_user and not current_user.has_perm("forum.change_post"):
            raise PermissionDenied
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment"] = self.get_object()
        context["is_staff"] = self.request.user.has_perm("forum.change_post")
        return context

    def get_queryset(self):
        comment = self.get_object()
        return (
            CommentEdit.objects.filter(comment=comment)
            .select_related("editor")
            .select_related("editor__profile")
            .select_related("deleted_by")
            .select_related("deleted_by__profile")
            .order_by("-date")
        )


class EditDetail(DetailView):
    model = CommentEdit
    context_object_name = "edit"
    template_name = "pages/edit_detail.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        response = super().dispatch(*args, **kwargs)
        current_user = self.request.user
        edit = self.get_object()
        if not edit.comment.author == current_user and not current_user.has_perm("forum.change_post"):
            raise PermissionDenied
        if edit.deleted_by:
            raise PermissionDenied
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment"] = self.get_object().comment
        context["is_staff"] = self.request.user.has_perm("forum.change_post")
        return context


@login_required
@can_write_and_read_now
@require_POST
def restore_edit(request, edit_pk):
    edit = get_object_or_404(CommentEdit, pk=edit_pk)
    comment = edit.comment

    if not comment.author == request.user and not request.user.has_perm("forum.change_post"):
        raise PermissionDenied

    if not comment.is_visible:  # comment was hidden
        raise PermissionDenied

    if edit.deleted_by:
        raise PermissionDenied

    new_edit = CommentEdit()
    new_edit.comment = comment
    new_edit.editor = request.user
    new_edit.original_text = comment.text
    new_edit.save()

    comment.update = datetime.now()
    comment.editor = request.user
    comment.update_content(
        edit.original_text, lambda m: messages.error(request, _("Erreurs dans le markdown: {}").format("\n- ".join(m)))
    )
    # remove hat if the author doesn't have it anymore
    if comment.hat and comment.hat not in comment.author.profile.get_hats():
        comment.hat = None
    comment.save()

    return redirect(comment.get_absolute_url())


@login_required
@permission_required("forum.change_post", raise_exception=True)
@require_POST
def delete_edit_content(request, edit_pk):
    edit = get_object_or_404(CommentEdit, pk=edit_pk)

    if edit.deleted_by:
        raise PermissionDenied

    edit.original_text = ""
    edit.deleted_by = request.user
    edit.deleted_at = datetime.now()
    edit.save()

    return redirect("comment-edits-history", comment_pk=edit.comment.pk)


def custom_error_500(request):
    """Custom view for 500 errors"""
    return render(request, "500.html", status=500)
