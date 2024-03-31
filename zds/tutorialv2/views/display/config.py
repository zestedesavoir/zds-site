from django.utils.translation import gettext_lazy as _

from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.models.versioned import VersionedContent


class AdministrationActionsState:
    def __init__(self, user, content: PublishableContent, versioned_content: VersionedContent, enabled=True):
        self.is_staff = user.has_perm("tutorialv2.change_publishablecontent")
        self.is_allowed = content.is_author(user) or self.is_staff
        self.requires_validation = content.requires_validation()
        self.version_is_public = versioned_content.is_public
        self.is_moderated = content.is_permanently_unpublished()
        self.in_public = content.in_public()
        self.enabled = enabled

    def show_block(self) -> bool:
        return (
            self.enabled
            and self.is_allowed
            and (
                self.show_versions_history_link()
                or self.show_events_history_link()
                or self.show_opinion_publish()
                or self.show_opinion_moderated()
                or self.show_gallery_link()
                or self.show_jsfiddle()
            )
        )

    def show_versions_history_link(self) -> bool:
        return self.is_allowed

    def show_events_history_link(self) -> bool:
        return self.is_allowed

    def show_opinion_publish(self) -> bool:
        return self.is_allowed and not self.version_is_public and not self.requires_validation and not self.is_moderated

    def show_opinion_moderated(self) -> bool:
        return self.is_allowed and not self.requires_validation and self.is_moderated

    def show_gallery_link(self) -> bool:
        return self.is_allowed

    def show_jsfiddle(self) -> bool:
        return self.enabled and self.is_staff and self.requires_validation


class PublicActionsState:
    messages = {
        "draft_is_same": _("La version brouillon est identique à cette version."),
        "draft_is_more_recent": _("La version brouillon est plus récente que cette version."),
        "public_is_same": _("La version publique est identique à cette version."),
        "export_content": _("Exports du contenu"),
    }

    def __init__(self, user, content: PublishableContent, versioned_content: VersionedContent):
        self.is_staff = user.has_perm("tutorialv2.change_publishablecontent")
        self.is_author_or_staff = content.is_author(user) or self.is_staff
        self.in_public = content.in_public()
        self.is_same_as_public = content.is_public(versioned_content.current_version)
        self.is_same_as_draft = not content.is_draft_more_recent_than_public()
        self.requires_validation = content.requires_validation()
        self.is_public_page = False
        self.enabled = True

    def show_block(self) -> bool:
        return (
            self.enabled
            and self.is_author_or_staff
            and (
                self.show_stats_link()
                or self.show_exports_request()
                or self.show_identical_public_version_message()
                or self.show_identical_draft_version_message()
                or self.show_more_recent_draft_version_link()
                or self.show_page_link()
                or self.show_public_page_message()
                or self.show_comparison_link()
                or self.show_content_revoke()
                or self.show_opinion_unpublish()
            )
        )

    def show_exports_request(self) -> bool:
        return self.is_author_or_staff and self.in_public and self.is_public_page

    def show_stats_link(self) -> bool:
        return self.is_author_or_staff and self.in_public

    def show_identical_public_version_message(self) -> bool:
        return self.is_author_or_staff and self.in_public and self.is_same_as_public and not self.is_public_page

    def show_more_recent_draft_version_link(self) -> bool:
        return self.is_author_or_staff and self.is_public_page and not self.is_same_as_draft

    def show_identical_draft_version_message(self) -> bool:
        return self.is_author_or_staff and self.is_public_page and self.is_same_as_draft

    def show_page_link(self) -> bool:
        return self.is_author_or_staff and self.in_public and not self.is_public_page

    def show_public_page_message(self) -> bool:
        return self.is_author_or_staff and self.in_public and self.is_public_page

    def show_comparison_link(self) -> bool:
        return self.is_author_or_staff and self.in_public and not self.is_same_as_public

    def show_content_revoke(self) -> bool:
        return self.is_staff and self.requires_validation and self.in_public

    def show_opinion_unpublish(self) -> bool:
        return self.is_author_or_staff and not self.requires_validation and self.in_public


class BetaActionsState:
    def __init__(
        self,
        user,
        content: PublishableContent,
        versioned_content: VersionedContent,
        enabled=False,
        is_beta_page=False,
    ):
        self.enabled = enabled
        self.is_allowed = content.is_author(user) or user.has_perm("tutorialv2.change_publishablecontent")
        self.can_content_be_beta = content.can_be_in_beta()
        self.is_content_in_beta = content.in_beta()
        self.is_version_beta = versioned_content.is_beta
        self.is_beta_page = is_beta_page
        self.requires_validation = content.requires_validation()

    def show_block(self) -> bool:
        return self.enabled and (
            self.show_identical_message()
            or self.show_beta_page_link()
            or self.show_comparison_with_beta()
            or self.show_activate()
            or self.show_update()
            or self.show_deactivate()
        )

    def _common_conditions(self) -> bool:
        return self.requires_validation and self.is_allowed

    def show_identical_message(self) -> bool:
        return self._common_conditions() and self.is_content_in_beta and self.is_version_beta

    def show_beta_page_link(self) -> bool:
        return self._common_conditions() and self.is_content_in_beta and not self.is_beta_page

    def show_comparison_with_beta(self) -> bool:
        return self._common_conditions() and self.is_content_in_beta and not self.is_version_beta

    def show_activate(self) -> bool:
        return self._common_conditions() and not self.is_content_in_beta

    def show_update(self) -> bool:
        return self._common_conditions() and self.is_content_in_beta and not self.is_version_beta

    def show_deactivate(self) -> bool:
        return self._common_conditions() and self.is_content_in_beta


class DraftActionsState:
    def __init__(self, user, content: PublishableContent, enabled=False, is_draft_page=False, is_container=False):
        self.is_allowed = content.is_author(user) or user.has_perm("tutorialv2.change_publishablecontent")
        self.enabled = enabled
        self.requires_validation = content.requires_validation()
        self.is_draft_page = is_draft_page
        self.is_container = is_container

    def enable_edit(self) -> bool:
        return self.enabled and self.is_allowed

    def show_draft_link(self) -> bool:
        return self.is_allowed and not self.is_draft_page

    def show_license_edit(self) -> bool:
        return self.enabled and self.is_allowed and not self.is_container

    def show_title_edit(self) -> bool:
        return self.enabled and self.is_allowed and not self.is_container

    def show_authors_management(self) -> bool:
        return self.enabled and self.is_allowed

    def show_categories_management(self) -> bool:
        return self.enabled and self.is_allowed

    def show_contributors_management(self) -> bool:
        return self.enabled and self.is_allowed

    def show_ready_to_publish(self) -> bool:
        return self.enabled and self.is_allowed and self.requires_validation

    def show_deletion_link(self) -> bool:
        return self.enabled and self.is_allowed

    def show_edit_content_link(self) -> bool:
        return self.enabled and self.is_allowed

    def show_import_link(self) -> bool:
        return self.enabled and self.is_allowed

    def show_empty_section_warnings(self) -> bool:
        return self.enabled and self.is_allowed


class OnlineState:
    def __init__(self, user, content: PublishableContent, enabled=False):
        self.enabled = enabled
        self.user_is_authenticated = user.is_authenticated
        self.requires_validation = content.requires_validation()
        self.is_obsolete = content.is_obsolete

    def show_dcmi_card(self) -> bool:
        return self.enabled

    def show_meta_image(self) -> bool:
        return self.enabled

    def show_meta_description(self) -> bool:
        return self.enabled

    def show_opengraph(self) -> bool:
        return self.enabled

    def show_canonical_link(self) -> bool:
        return self.enabled

    def show_obsolescence_warning(self) -> bool:
        return self.enabled

    def show_follow_actions(self) -> bool:
        return self.enabled and self.user_is_authenticated

    def show_propose_feature(self) -> bool:
        return self.enabled and self.user_is_authenticated and self.requires_validation and not self.is_obsolete

    def show_social_buttons(self) -> bool:
        return self.enabled

    def show_suggestions(self) -> bool:
        return self.enabled

    def show_contact_authors(self) -> bool:
        return self.enabled and self.user_is_authenticated

    def show_opinion_list_links(self) -> bool:
        return self.enabled and not self.requires_validation

    def enable_update_date_online_mode(self) -> bool:
        return self.enabled

    def enable_authors_online_mode(self) -> bool:
        return self.enabled

    def show_content_pager(self) -> bool:
        return self.enabled

    def show_comments(self) -> bool:
        return self.enabled

    def show_rendered_source(self) -> bool:
        return self.enabled

    def show_reading_time(self) -> bool:
        return self.enabled

    def show_exports(self) -> bool:
        return self.enabled


class ValidationActions:
    messages = {
        "validation_is_same": _("La version en validation est identique à cette version."),
    }

    def __init__(self, user, content: PublishableContent, versioned_content: VersionedContent):
        self.is_staff = user.has_perm("tutorialv2.change_publishablecontent")
        self.is_author_or_staff = content.is_author(user) or self.is_staff
        self.in_validation = content.in_validation()
        self.version_is_validation = content.is_validation(versioned_content.current_version)
        self.requires_validation = content.requires_validation()
        self.in_public = content.in_public()
        self.content_is_picked = content.is_picked()
        self.enabled = True
        self.is_validation_page = False
        validation = content.get_validation()
        self.reserved = (validation is not None) and validation.is_pending_valid()

    def show_validation_actions(self) -> bool:
        return self.enabled and (
            self.show_ask_validation()
            or self.show_cancel_validation()
            or self.show_identical_message()
            or self.show_validation_admin()
            or self.show_update_validation()
            or self.show_validation_history()
            or self.show_validation_link()
            or self.show_comparison_with_validation()
            or self.show_opinion_convert()
            or self.show_opinion_pick()
            or self.show_opinion_unpick()
            or self.show_opinion_moderate()
            or self.show_moderation_history()
        )

    def show_ask_validation(self) -> bool:
        return self.enabled and self.is_author_or_staff and self.requires_validation and not self.in_validation

    def show_cancel_validation(self) -> bool:
        return self.enabled and self.is_author_or_staff and self.in_validation

    def show_identical_message(self) -> bool:
        return self.enabled and self.is_author_or_staff and self.version_is_validation and not self.is_validation_page

    def show_validation_admin(self) -> bool:
        return self.enabled and self.is_staff

    def show_update_validation(self) -> bool:
        return self.enabled and self.is_author_or_staff and self.in_validation and not self.version_is_validation

    def show_validation_history(self) -> bool:
        return self.enabled and self.is_staff and self.requires_validation

    def show_validation_link(self) -> bool:
        return self.enabled and self.is_author_or_staff and self.in_validation

    def show_comparison_with_validation(self) -> bool:
        return self.enabled and self.is_author_or_staff and self.in_validation and not self.version_is_validation

    def show_opinion_convert(self) -> bool:
        return self.enabled and self.is_staff and not self.requires_validation and self.in_public

    def _common_moderation_conditions(self) -> bool:
        return self.enabled and self.is_staff and not self.requires_validation

    def show_opinion_pick(self) -> bool:
        return self._common_moderation_conditions() and self.in_public and not self.content_is_picked

    def show_opinion_unpick(self) -> bool:
        return self._common_moderation_conditions() and self.content_is_picked

    def show_opinion_moderate(self) -> bool:
        return self._common_moderation_conditions() and self.in_public

    def show_moderation_history(self) -> bool:
        return self._common_moderation_conditions()


class ValidationInfo:
    def __init__(self, user, content: PublishableContent, versioned_content: VersionedContent, enabled=True):
        self.enabled = enabled
        self.is_staff = user.has_perm("tutorialv2.change_publishablecontent")
        self.is_author_or_staff = content.is_author(user) or self.is_staff
        self.in_validation = content.in_validation()
        self.version_is_validation = content.is_validation(versioned_content.current_version)
        self.requires_validation = content.requires_validation()
        validation = content.get_validation()
        self.reserved = (validation is not None) and validation.is_pending_valid()

    def _common_conditions(self) -> bool:
        return self.enabled and self.is_author_or_staff and self.requires_validation and self.in_validation

    def current_version_and_reserved(self) -> bool:
        return self._common_conditions() and self.version_is_validation and self.reserved

    def current_version_and_waiting_validator(self) -> bool:
        return self._common_conditions() and self.version_is_validation and not self.reserved

    def other_version_and_reserved(self) -> bool:
        return self._common_conditions() and not self.version_is_validation and self.reserved

    def other_version_and_waiting_validator(self) -> bool:
        return self._common_conditions() and not self.version_is_validation and not self.reserved


class BetaInfo:
    def __init__(self, user, content: PublishableContent, versioned_content: VersionedContent, enabled=True):
        self.enabled = enabled
        self.is_allowed = content.is_author(user) or user.has_perm("tutorialv2.change_publishablecontent")
        self.requires_validation = content.requires_validation()
        self.version_is_beta = content.is_beta(versioned_content.current_version)
        self.in_beta = content.in_beta()

    def _common_conditions(self) -> bool:
        return self.enabled and self.is_allowed and self.requires_validation and self.in_beta

    def current_version(self) -> bool:
        return self._common_conditions() and self.version_is_beta

    def other_version(self) -> bool:
        return self._common_conditions() and not self.version_is_beta


class AlertsConfig:
    def __init__(self, user, content: PublishableContent, enabled=False):
        self.requires_validation = content.requires_validation()
        # This is from the SolveContentAlert view at the time of writing.
        # A specific permission would be better.
        self.is_staff = user.has_perm("tutorialv2.change_contentreaction")
        self.enabled = enabled

    def show_alerts(self) -> bool:
        return self.enabled and self.is_staff and not self.requires_validation

    def show_alert_button(self) -> bool:
        return self.enabled and not self.requires_validation


class InfoConfig:
    def __init__(self, user, content: PublishableContent, versioned_content: VersionedContent, enabled=True):
        self.enabled = enabled
        self.is_allowed = content.is_author(user) or user.has_perm("tutorialv2.change_publishablecontent")
        self.requires_validation = content.requires_validation()
        self.moderated = content.is_permanently_unpublished()
        self.promoted = content.converted_to is not None
        self.is_beta = versioned_content.is_beta
        self.in_validation = content.in_validation()
        self.show_warn_typo = False

    def show_opinion_promotion(self) -> bool:
        return self.enabled and not self.requires_validation and self.promoted

    def show_opinion_moderation_warning(self) -> bool:
        return self.enabled and not self.requires_validation and self.moderated

    def show_help_info(self) -> bool:
        return self.enabled and self.requires_validation


class ViewConfig:
    def __init__(self, user, content: PublishableContent, versioned_content: VersionedContent):
        self.beta_actions = BetaActionsState(user, content, versioned_content)
        self.public_actions = PublicActionsState(user, content, versioned_content)
        self.administration_actions = AdministrationActionsState(user, content, versioned_content)
        self.draft_actions = DraftActionsState(user, content)
        self.online_config = OnlineState(user, content)
        self.validation_actions = ValidationActions(user, content, versioned_content)
        self.alerts_config = AlertsConfig(user, content)
        self.info_config = InfoConfig(user, content, versioned_content)
        self.validation_info = ValidationInfo(user, content, versioned_content)
        self.beta_info = BetaInfo(user, content, versioned_content)
        self.enable_editorialization = False


class ConfigForContentDraftView(ViewConfig):
    def __init__(self, user, content: PublishableContent, versioned_content: VersionedContent):
        super().__init__(user, content, versioned_content)
        self.beta_actions.enabled = True
        self.draft_actions.enabled = True
        self.draft_actions.is_draft_page = True
        self.online_config.enabled = False
        self.info_config.enabled = True
        self.enable_editorialization = content.is_author(user) or user.has_perm("tutorialv2.change_publishablecontent")


class ConfigForContainerDraftView(ConfigForContentDraftView):
    def __init__(self, user, content: PublishableContent, versioned_content: VersionedContent):
        super().__init__(user, content, versioned_content)
        self.draft_actions.is_container = True


class ConfigForVersionView(ViewConfig):
    def __init__(self, user, content: PublishableContent, versioned_content: VersionedContent):
        super().__init__(user, content, versioned_content)
        self.beta_actions.enabled = False
        self.draft_actions.enabled = False
        self.draft_actions.is_draft_page = False
        self.online_config.enabled = False
        self.info_config.enabled = True
        self.public_actions.enabled = False
        self.administration_actions.enabled = False
        self.validation_actions.enabled = False


class ConfigForOnlineView(ViewConfig):
    def __init__(self, user, content: PublishableContent, versioned_content: VersionedContent):
        super().__init__(user, content, versioned_content)
        self.beta_actions.enabled = False
        self.public_actions.is_public_page = True
        self.administration_actions.enabled = False
        self.validation_actions.enabled = True
        self.online_config.enabled = True
        self.alerts_config.enabled = True
        self.info_config.show_warn_typo = True
        self.validation_info.enabled = False
        self.beta_info.enabled = False
        self.enable_editorialization = content.is_author(user) or user.has_perm("tutorialv2.change_publishablecontent")


class ConfigForBetaView(ViewConfig):
    def __init__(self, user, content: PublishableContent, versioned_content: VersionedContent):
        super().__init__(user, content, versioned_content)
        self.beta_actions.enabled = True
        self.beta_actions.is_beta_page = True
        self.administration_actions.enabled = False
        self.validation_actions.enabled = False
        self.online_config.enabled = False
        self.info_config.show_warn_typo = True


class ConfigForValidationView(ViewConfig):
    def __init__(self, user, content: PublishableContent, versioned_content: VersionedContent):
        super().__init__(user, content, versioned_content)
        self.beta_actions.enabled = False
        self.administration_actions.enabled = False
        self.validation_actions.enabled = True
        self.validation_actions.show_validation_link = False
        self.online_config.enabled = False
        self.info_config.show_warn_typo = True
        self.validation_actions.is_validation_page = True
