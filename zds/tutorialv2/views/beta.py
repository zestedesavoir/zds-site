from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from zds.forum.models import Forum, Topic, mark_read
from zds.forum.utils import create_topic, lock_topic, send_post, unlock_topic
from zds.member.decorator import LoggedWithReadWriteHability
from zds.member.utils import get_bot_account
from zds.mp.models import filter_reachable
from zds.mp.utils import send_message_mp, send_mp
from zds.notification.models import TopicAnswerSubscription
from zds.tutorialv2 import signals
from zds.tutorialv2.forms import BetaForm
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models.database import PublishableContent
from zds.utils.models import get_hat_from_settings


class ManageBetaContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    """
    Depending of the value of `self.action`, this class will behave differently;
    - if 'set', it will active (of update) the beta
    - if 'inactive', it will inactive the beta on the tutorial
    """

    model = PublishableContent
    form_class = BetaForm
    authorized_for_staff = True

    action = None

    def _get_all_tags(self):
        return list(self.object.tags.all())

    def _create_beta_topic(self, msg, beta_version, _type, tags):
        topic_title = beta_version.title
        _tags = f"[beta][{_type}]"
        i = 0
        max_len = Topic._meta.get_field("title").max_length

        while i < len(tags) and len(topic_title) + len(_tags) + len(tags[i].title) + 2 < max_len:
            _tags += f"[{tags[i]}]"
            i += 1
        forum = get_object_or_404(Forum, pk=settings.ZDS_APP["forum"]["beta_forum_id"])
        topic = create_topic(
            request=self.request,
            author=self.request.user,
            forum=forum,
            title=topic_title,
            subtitle=f"{beta_version.description}",
            text=msg,
            related_publishable_content=self.object,
        )
        topic.save()
        # make all authors follow the topic:
        for author in self.object.authors.all():
            TopicAnswerSubscription.objects.get_or_create_active(author, topic)
            mark_read(topic, author)

        return topic

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        beta_version = self.versioned_object
        sha_beta = beta_version.current_version

        # topic of the beta version:
        topic = self.object.beta_topic

        if topic:
            if topic.forum_id != settings.ZDS_APP["forum"]["beta_forum_id"]:
                # if the topic is moved from the beta forum, then a new one is created instead
                topic = None

        _type = self.object.type.lower()
        if _type == "tutorial":
            _type = _("tutoriel")
        elif _type == "opinion":
            raise PermissionDenied

        # perform actions:
        if self.action == "inactive":
            self.object.sha_beta = None

            msg_post = render_to_string(
                "tutorialv2/messages/beta_desactivate.md", {"content": beta_version, "type": _type}
            )
            send_post(self.request, topic, self.request.user, msg_post)
            lock_topic(topic)
            signals.beta_management.send(
                sender=self.__class__,
                content=self.object,
                performer=self.request.user,
                version=sha_beta,
                action="deactivate",
            )

        elif self.action == "set":
            already_in_beta = self.object.in_beta()
            all_tags = []

            if not already_in_beta or self.object.sha_beta != sha_beta:
                self.object.sha_beta = sha_beta
                self.versioned_object.in_beta = True
                self.versioned_object.sha_beta = sha_beta

                msg = render_to_string(
                    "tutorialv2/messages/beta_activate_topic.md",
                    {
                        "content": beta_version,
                        "type": _type,
                        "url": settings.ZDS_APP["site"]["url"] + self.versioned_object.get_absolute_url_beta(),
                    },
                )

                if not topic:
                    # if first time putting the content in beta, send a message on the forum and a PM

                    # find tags
                    all_tags = self._get_all_tags()
                    topic = self._create_beta_topic(msg, beta_version, _type, all_tags)

                    bot = get_bot_account()
                    msg_pm = render_to_string(
                        "tutorialv2/messages/beta_activate_pm.md",
                        {
                            "content": beta_version,
                            "type": _type,
                            "url": settings.ZDS_APP["site"]["url"] + topic.get_absolute_url(),
                            "user": self.request.user,
                        },
                    )
                    if not self.object.validation_private_message:
                        recipients = filter_reachable(self.object.authors.all())
                        self.object.validation_private_message = send_mp(
                            bot,
                            recipients,
                            self.object.validation_message_title,
                            beta_version.title,
                            msg_pm,
                            send_by_mail=False,
                            leave=True,
                            hat=get_hat_from_settings("validation"),
                        )
                        self.object.save()
                    else:
                        send_message_mp(
                            bot, self.object.validation_private_message, msg, hat=get_hat_from_settings("validation")
                        )

                # When the anti-spam triggers (because the author of the
                # message posted themselves within the last 15 minutes),
                # it is likely that we want to avoid to generate a duplicated
                # post that couldn't be deleted. We hence avoid to add another
                # message to the topic.

                else:
                    all_tags = self._get_all_tags()

                    if not already_in_beta:
                        unlock_topic(topic)
                        msg_post = render_to_string(
                            "tutorialv2/messages/beta_reactivate.md",
                            {
                                "content": beta_version,
                                "type": _type,
                                "url": settings.ZDS_APP["site"]["url"] + self.versioned_object.get_absolute_url_beta(),
                            },
                        )
                        topic = send_post(self.request, topic, self.request.user, msg_post)
                    elif not topic.antispam():
                        msg_post = render_to_string(
                            "tutorialv2/messages/beta_update.md",
                            {
                                "content": beta_version,
                                "type": _type,
                                "url": settings.ZDS_APP["site"]["url"] + self.versioned_object.get_absolute_url_beta(),
                            },
                        )
                        topic = send_post(self.request, topic, self.request.user, msg_post)

                # make sure that all authors follow the topic:
                for author in self.object.authors.all():
                    TopicAnswerSubscription.objects.get_or_create_active(author, topic)
                    mark_read(topic, author)

            # finally set the tags on the topic
            if topic:
                topic.tags.clear()
                for tag in all_tags:
                    topic.tags.add(tag)
                topic.save()

            signals.beta_management.send(
                sender=self.__class__,
                content=self.object,
                performer=self.request.user,
                version=sha_beta,
                action="activate",
            )

        self.object.save()  # we should prefer .update but it needs a huge refactoring

        self.success_url = self.versioned_object.get_absolute_url(version=sha_beta)

        if self.object.is_beta(sha_beta):
            self.success_url = self.versioned_object.get_absolute_url_beta()

        return super().form_valid(form)
