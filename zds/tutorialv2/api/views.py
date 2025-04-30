import contextlib
from pathlib import Path

from django.db.models.query import prefetch_related_objects
from django.http import Http404
from django.utils import translation
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.fields import empty
from rest_framework.generics import ListAPIView, UpdateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.serializers import BooleanField, CharField, Serializer
from rest_framework.views import APIView

from zds.member.api.permissions import CanReadAndWriteNowOrReadOnly, IsAuthorOrStaff, IsNotOwnerOrReadOnly
from zds.tutorialv2.api.serializers import PublicationEventSerializer
from zds.tutorialv2.models.database import ContentReaction, PublicationEvent, PublishableContent
from zds.tutorialv2.publication_utils import PublicatorRegistry
from zds.tutorialv2.utils import search_container_or_404
from zds.utils.api.views import KarmaView


class ContainerReadinessSerializer(Serializer):
    parent_container_slug = CharField(allow_blank=True, allow_null=True, required=False)
    container_slug = CharField(required=True)
    ready_to_publish = BooleanField(required=True)

    def run_validation(self, data=empty):
        init = super().run_validation(data)
        if not init:
            return init
        if not data.get("parent_container_slug", ""):
            init.pop("parent_container_slug", "")
        return init

    def save(self, **kwargs):
        if not self.validated_data:
            self.is_valid(True)
        versioned = self.instance.load_version()
        container = search_container_or_404(versioned, self.validated_data)
        container.ready_to_publish = self.validated_data["ready_to_publish"]
        sha = versioned.repo_update(
            versioned.title,
            versioned.get_introduction(),
            versioned.get_conclusion(),
            commit_message=_("{} est {} à la publication.").format(
                container.get_path(True),
                _("prêt") if container.ready_to_publish else _("ignoré"),
            ),
        )
        PublishableContent.objects.filter(pk=self.instance.pk).update(sha_draft=sha)

    def to_representation(self, instance):
        return {}


class ContentReactionKarmaView(KarmaView):
    queryset = ContentReaction.objects.all()
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        CanReadAndWriteNowOrReadOnly,
        IsNotOwnerOrReadOnly,
    )


class ContainerPublicationReadinessView(UpdateAPIView):
    permission_classes = (IsAuthorOrStaff,)
    serializer_class = ContainerReadinessSerializer

    def get_queryset(self):
        return PublishableContent.objects.prefetch_related("authors").filter(pk=int(self.kwargs.get("pk", 0))).first()

    def get_object(self):
        content = self.get_queryset()
        if not content:
            raise Http404()
        self.check_object_permissions(self.request, object)
        return content


class ExportView(APIView):
    permission_classes = (IsAuthorOrStaff,)
    _object = None

    def get_object(self):  # required by IsAuthorOrStaff
        if not self._object:
            self._object = get_object_or_404(PublishableContent.objects, pk=int(self.kwargs.get("pk", 0)))
        return self._object

    def ensure_directories(self, content: PublishableContent):
        final_directory = Path(content.public_version.get_extra_contents_directory())
        building_directory = Path(str(final_directory.parent) + "__building", final_directory.name)
        with contextlib.suppress(FileExistsError):
            final_directory.mkdir(parents=True)
        with contextlib.suppress(FileExistsError):
            building_directory.mkdir(parents=True)
        return building_directory, final_directory

    def post(self, request, *args, **kwargs):
        try:
            publishable_content = self.get_object()
            if not publishable_content.public_version:
                raise Http404("Not public content")
            self.ensure_directories(publishable_content)
            PublicatorRegistry.get("watchdog").publish_from_published_content(publishable_content.public_version)
        except ValueError:
            return Response({}, status=status.HTTP_400_BAD_REQUEST, headers={})
        else:
            return Response({}, status=status.HTTP_201_CREATED, headers={})


class ExportsView(ListAPIView):
    """
    Lists the most recent exports for this content, and their status.
    """

    serializer_class = PublicationEventSerializer
    pagination_class = None

    def get_queryset(self):
        # Retrieves the latest entry for each `format_requested`, for our content.
        # The `latest_events` sub-request retieves all events for the current content, and
        # and annotates them with their row number if we would select them by requested format,
        # ordered by descending date. The first one by date with the PDF type would be annotated
        # 1, the second with PDF, 2, etc.
        # The outer request selects everything in the inner request, but filtering only the first
        # row for each format, keeping only the latest record for each type for this content.
        # We have to use a sub-request as the SQL spec forbides to filter on a windowed element
        # directly.
        #
        # This uses raw SQL because even if Django supports windowed requests, it does not allow
        # to select _from_ a subrequest (« SELECT * FROM (SELECT … ) WHERE … »).
        exports = PublicationEvent.objects.raw(
            """
            WITH latest_events AS (
                SELECT p.*, ROW_NUMBER() OVER (PARTITION BY format_requested ORDER BY date DESC) AS row
                FROM tutorialv2_publicationevent AS p
                INNER JOIN tutorialv2_publishedcontent published ON (p.published_object_id = published.id)
                WHERE published.content_id = %s
            )
            SELECT * FROM latest_events WHERE row = 1""",
            [int(self.kwargs.get("pk", 0))],
        )

        prefetch_related_objects(exports, "published_object")

        return exports
