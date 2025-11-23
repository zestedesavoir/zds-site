import logging

from django.conf import settings
from django.http import Http404
from git import GitCommandError, objects
from gitdb.exc import BadName, BadObject

from zds.member.decorator import LoggedWithReadWriteHability
from zds.tutorialv2.mixins import SingleContentDetailViewMixin
from zds.tutorialv2.models.database import PublishableContent
from zds.utils.paginator import make_pagination

logger = logging.getLogger(__name__)


class DisplayHistory(LoggedWithReadWriteHability, SingleContentDetailViewMixin):
    """
    Display the whole modification history.
    This class has no reason to be adapted to any content type.
    """

    model = PublishableContent
    template_name = "tutorialv2/view/history.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        repo = self.versioned_object.repository
        commits = list(objects.commit.Commit.iter_items(repo, "HEAD"))

        # Pagination of commits
        make_pagination(
            context, self.request, commits, settings.ZDS_APP["content"]["commits_per_page"], context_list_name="commits"
        )

        # Git empty tree is 4b825dc642cb6eb9a060e54bf8d69288fbee4904, see
        # http://stackoverflow.com/questions/9765453/gits-semi-secret-empty-tree
        context["empty_sha"] = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

        return context


class DisplayDiff(LoggedWithReadWriteHability, SingleContentDetailViewMixin):
    """
    Display the difference between two versions of a content.
    The left version is given in a GET query parameter named from, the right one with to.
    This class has no reason to be adapted to any content type.
    """

    model = PublishableContent
    template_name = "tutorialv2/view/diff.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "from" not in self.request.GET:
            raise Http404("Paramètre GET 'from' manquant.")
        if "to" not in self.request.GET:
            raise Http404("Paramètre GET 'to' manquant.")

        # open git repo and find diff between two versions
        repo = self.versioned_object.repository
        try:
            # repo.commit raises BadObject or BadName if invalid SHA
            commit_from = repo.commit(self.request.GET["from"])
            commit_to = repo.commit(self.request.GET["to"])
            # commit_to.diff raises GitErrorCommand if 00..00 SHA for instance
            tdiff = commit_to.diff(commit_from, R=True)
        except (GitCommandError, BadName, BadObject, ValueError) as git_error:
            logger.warning(git_error)
            raise Http404(
                "En traitant le contenu {} git a lancé une erreur de type {}:{}".format(
                    self.object.title, type(git_error), str(git_error)
                )
            )

        context["commit_from"] = commit_from
        context["commit_to"] = commit_to
        context["modified"] = tdiff.iter_change_type("M")
        context["added"] = tdiff.iter_change_type("A")
        context["deleted"] = tdiff.iter_change_type("D")
        context["renamed"] = tdiff.iter_change_type("R")

        return context
