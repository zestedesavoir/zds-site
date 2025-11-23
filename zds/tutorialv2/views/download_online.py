import os

from django.http import Http404, HttpResponsePermanentRedirect

from zds.tutorialv2.mixins import DownloadViewMixin, MustRedirect, SingleOnlineContentViewMixin


class DownloadOnlineContent(SingleOnlineContentViewMixin, DownloadViewMixin):
    """Views that allow users to download 'extra contents' of the public version"""

    requested_file = None
    allowed_types = ["md", "html", "pdf", "epub", "zip", "tex"]

    mimetypes = {
        "html": "text/html",
        "md": "text/plain",
        "pdf": "application/pdf",
        "epub": "application/epub+zip",
        "zip": "application/zip",
        "tex": "application/x-latex",
    }

    def get_redirect_url(self, public_version):
        return public_version.content.public_version.get_absolute_url_to_extra_content(self.requested_file)

    def get(self, context, **response_kwargs):
        # fill the variables
        try:
            self.public_content_object = self.get_public_object()
        except MustRedirect as redirect_url:
            return HttpResponsePermanentRedirect(redirect_url.url)

        self.object = self.get_object()
        self.versioned_object = self.get_versioned_object()

        # check that type is ok
        if self.requested_file not in self.allowed_types:
            raise Http404("Le type du fichier n'est pas permis.")

        # check existence
        if not self.public_content_object.has_type(self.requested_file):
            raise Http404("Le type n'existe pas.")

        if self.requested_file == "md" and not self.is_author and not self.is_staff:
            # download markdown is only for staff and author
            raise Http404("Seul le staff et l'auteur peuvent télécharger la version Markdown du contenu.")

        # set mimetype accordingly
        self.mimetype = self.mimetypes[self.requested_file]

        # set UTF-8 response for markdown
        if self.requested_file == "md":
            self.mimetype += "; charset=utf-8"

        return super().get(context, **response_kwargs)

    def get_filename(self):
        return self.public_content_object.content_public_slug + "." + self.requested_file

    def get_contents(self):
        path = os.path.join(self.public_content_object.get_extra_contents_directory(), self.get_filename())
        try:
            response = open(path, "rb").read()
        except OSError:
            raise Http404("Le fichier n'existe pas.")

        return response


class DownloadOnlineArticle(DownloadOnlineContent):
    current_content_type = "ARTICLE"


class DownloadOnlineTutorial(DownloadOnlineContent):
    current_content_type = "TUTORIAL"


class DownloadOnlineOpinion(DownloadOnlineContent):
    current_content_type = "OPINION"
