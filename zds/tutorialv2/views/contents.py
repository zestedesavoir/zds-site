import logging
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView
from uuslug import slugify

from zds.gallery.models import Gallery, Image
from zds.member.decorator import LoggedWithReadWriteHability, LoginRequiredMixin
from zds.member.models import Profile
from zds.tutorialv2.forms import ContentForm, JsFiddleActivationForm, AskValidationForm, AcceptValidationForm, \
    RejectValidationForm, RevokeValidationForm, WarnTypoForm, CancelValidationForm, PublicationForm, \
    UnpublicationForm, ContributionForm, SearchSuggestionForm, EditContentLicenseForm, EditContentTagsForm
from zds.tutorialv2.mixins import SingleContentDetailViewMixin, SingleContentFormViewMixin, SingleContentViewMixin, \
    FormWithPreview
from zds.tutorialv2.models.database import PublishableContent, Validation, ContentContribution, ContentSuggestion
from zds.tutorialv2.utils import init_new_repo
from zds.tutorialv2.views.authors import RemoveAuthorFromContent
from zds.utils.models import get_hat_from_settings
from zds.utils.mps import send_mp, send_message_mp

logger = logging.getLogger(__name__)


class CreateContent(LoggedWithReadWriteHability, FormWithPreview):
    """
    Handle content creation. Since v22 a licence must be explicitly selected
    instead of defaulting to "All rights reserved". Users can however
    set a default licence in their profile.
    """
    template_name = 'tutorialv2/create/content.html'
    model = PublishableContent
    form_class = ContentForm
    content = None
    created_content_type = 'TUTORIAL'

    def get_form(self, form_class=ContentForm):
        form = super(CreateContent, self).get_form(form_class)
        form.initial['type'] = self.created_content_type
        return form

    def get_context_data(self, **kwargs):
        context = super(CreateContent, self).get_context_data(**kwargs)
        context['editorial_line_link'] = settings.ZDS_APP['content']['editorial_line_link']
        context['site_name'] = settings.ZDS_APP['site']['literal_name']
        return context

    def form_valid(self, form):

        # create the object:
        self.content = PublishableContent()
        self.content.title = form.cleaned_data['title']
        self.content.description = form.cleaned_data['description']
        self.content.type = form.cleaned_data['type']
        self.content.licence = self.request.user.profile.licence  # Use the preferred license of the user if it exists
        self.content.source = form.cleaned_data['source']
        self.content.creation_date = datetime.now()

        # Creating the gallery
        gal = Gallery()
        gal.title = form.cleaned_data['title']
        gal.slug = slugify(form.cleaned_data['title'])
        gal.pubdate = datetime.now()
        gal.save()

        self.content.gallery = gal
        self.content.save()
        # create image:
        if 'image' in self.request.FILES:
            img = Image()
            img.physical = self.request.FILES['image']
            img.gallery = gal
            img.title = self.request.FILES['image']
            img.slug = slugify(self.request.FILES['image'].name)
            img.pubdate = datetime.now()
            img.save()
            self.content.image = img

        self.content.save()

        # We need to save the content before changing its author list since it's a many-to-many relationship
        self.content.authors.add(self.request.user)

        self.content.ensure_author_gallery()
        self.content.save(force_slug_update=False)
        # Add subcategories on tutorial
        for subcat in form.cleaned_data['subcategory']:
            self.content.subcategory.add(subcat)

        self.content.save(force_slug_update=False)

        # create a new repo :
        init_new_repo(self.content,
                      form.cleaned_data['introduction'],
                      form.cleaned_data['conclusion'],
                      form.cleaned_data['msg_commit'])

        return super(CreateContent, self).form_valid(form)

    def get_success_url(self):
        return reverse('content:view', args=[self.content.pk, self.content.slug])


class DisplayContent(LoginRequiredMixin, SingleContentDetailViewMixin):
    """Base class that can show any content in any state"""

    model = PublishableContent
    template_name = 'tutorialv2/view/content.html'
    must_be_author = False  # as in beta state anyone that is logged can access to it
    only_draft_version = False

    def get_forms(self, context):
        """get all the auxiliary forms about validation, js fiddle..."""

        validation = Validation.objects.filter(content__pk=self.object.pk) \
            .order_by('-date_proposition') \
            .first()

        form_js = JsFiddleActivationForm(initial={'js_support': self.object.js_support})

        context['formAskValidation'] = AskValidationForm(
            content=self.versioned_object, initial={'source': self.object.source, 'version': self.sha})

        if validation:
            context['formValid'] = AcceptValidationForm(validation, initial={'source': self.object.source})
            context['formReject'] = RejectValidationForm(validation)
            context['formCancel'] = CancelValidationForm(validation)

        if self.versioned_object.sha_public:
            context['formRevokeValidation'] = RevokeValidationForm(
                self.versioned_object, initial={'version': self.versioned_object.sha_public})
            context['formUnpublication'] = UnpublicationForm(
                self.versioned_object, initial={'version': self.versioned_object.sha_public})

        if self.versioned_object.is_beta:
            context['formWarnTypo'] = WarnTypoForm(self.versioned_object, self.versioned_object, public=False)

        context['validation'] = validation
        context['formJs'] = form_js
        context['form_edit_license'] = EditContentLicenseForm(self.versioned_object)
        context['form_edit_tags'] = EditContentTagsForm(self.versioned_object, self.object)

        if self.versioned_object.requires_validation:
            context['formPublication'] = PublicationForm(self.versioned_object, initial={'source': self.object.source})
        else:
            context['formPublication'] = None

    def get_context_data(self, **kwargs):
        context = super(DisplayContent, self).get_context_data(**kwargs)

        # check whether this tuto support js fiddle
        if self.object.js_support:
            is_js = 'js'
        else:
            is_js = ''
        context['is_js'] = is_js

        self.get_forms(context)

        context['gallery'] = self.object.gallery
        context['public_content_object'] = self.public_content_object
        if self.object.type.lower() != 'opinion':
            context['formAddReviewer'] = ContributionForm(content=self.object)
            context['contributions'] = ContentContribution\
                .objects\
                .filter(content=self.object)\
                .order_by('contribution_role__position')
            context['content_suggestions'] = ContentSuggestion \
                .objects \
                .filter(publication=self.object)
            excluded_for_search = [str(x.suggestion.pk) for x in context['content_suggestions']]
            excluded_for_search.append(str(self.object.pk))
            context['formAddSuggestion'] = SearchSuggestionForm(content=self.object,
                                                                initial={'excluded_pk': ','.join(excluded_for_search)})

        return context


class EditContent(LoggedWithReadWriteHability, SingleContentFormViewMixin, FormWithPreview):
    template_name = 'tutorialv2/edit/content.html'
    model = PublishableContent
    form_class = ContentForm

    def get_initial(self):
        """rewrite function to pre-populate form"""
        initial = super(EditContent, self).get_initial()
        versioned = self.versioned_object

        initial['title'] = versioned.title
        initial['description'] = versioned.description
        initial['type'] = versioned.type
        initial['introduction'] = versioned.get_introduction()
        initial['conclusion'] = versioned.get_conclusion()
        initial['source'] = versioned.source
        initial['subcategory'] = self.object.subcategory.all()
        initial['last_hash'] = versioned.compute_hash()

        return initial

    def get_context_data(self, **kwargs):
        context = super(EditContent, self).get_context_data(**kwargs)
        if 'preview' not in self.request.POST:
            context['gallery'] = self.object.gallery

        return context

    def form_valid(self, form):
        versioned = self.versioned_object
        publishable = self.object

        # check if content has changed:
        current_hash = versioned.compute_hash()
        if current_hash != form.cleaned_data['last_hash']:
            data = form.data.copy()
            data['last_hash'] = current_hash
            data['introduction'] = versioned.get_introduction()
            data['conclusion'] = versioned.get_conclusion()
            form.data = data
            messages.error(self.request, _('Une nouvelle version a été postée avant que vous ne validiez.'))
            return self.form_invalid(form)

        # Forbid removing all categories of a validated content
        if publishable.in_public() and not form.cleaned_data['subcategory']:
            messages.error(self.request,
                           _('Vous devez choisir au moins une catégorie, car ce contenu est déjà publié.'))
            return self.form_invalid(form)

        # first, update DB (in order to get a new slug if needed)
        title_is_changed = publishable.title != form.cleaned_data['title']
        publishable.title = form.cleaned_data['title']
        publishable.description = form.cleaned_data['description']
        publishable.source = form.cleaned_data['source']

        publishable.update_date = datetime.now()

        # update gallery and image:
        gal = Gallery.objects.filter(pk=publishable.gallery.pk)
        gal.update(title=publishable.title)
        gal.update(slug=slugify(publishable.title))
        gal.update(update=datetime.now())

        if 'image' in self.request.FILES:
            img = Image()
            img.physical = self.request.FILES['image']
            img.gallery = publishable.gallery
            img.title = self.request.FILES['image']
            img.slug = slugify(self.request.FILES['image'].name)
            img.pubdate = datetime.now()
            img.save()
            publishable.image = img

        publishable.save(force_slug_update=title_is_changed)
        logger.debug('content %s updated, slug is %s', publishable.pk, publishable.slug)
        # now, update the versioned information
        versioned.description = form.cleaned_data['description']

        sha = versioned.repo_update_top_container(form.cleaned_data['title'],
                                                  publishable.slug,
                                                  form.cleaned_data['introduction'],
                                                  form.cleaned_data['conclusion'],
                                                  form.cleaned_data['msg_commit'])
        logger.debug('slug consistency after repo update repo=%s db=%s', versioned.slug, publishable.slug)
        # update relationships :
        publishable.sha_draft = sha

        publishable.subcategory.clear()
        for subcat in form.cleaned_data['subcategory']:
            publishable.subcategory.add(subcat)

        publishable.save(force_slug_update=False)

        self.success_url = reverse('content:view', args=[publishable.pk, publishable.slug])
        return super().form_valid(form)


class EditContentLicense(LoginRequiredMixin, SingleContentFormViewMixin):
    modal_form = True
    model = PublishableContent
    form_class = EditContentLicenseForm
    success_message_license = _('La licence de la publication a bien été changée.')
    success_message_profile_update = _('Votre licence préférée a bien été mise à jour.')

    def get_form_kwargs(self):
        kwargs = super(EditContentLicense, self).get_form_kwargs()
        kwargs['versioned_content'] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        publishable = self.object

        # Update license in database
        publishable.licence = form.cleaned_data['license']
        publishable.update_date = datetime.now()
        publishable.save(force_slug_update=False)

        # Update license in repository
        self.versioned_object.licence = form.cleaned_data['license']
        sha = self.versioned_object.repo_update_top_container(
            publishable.title,
            publishable.slug,
            self.versioned_object.get_introduction(),
            self.versioned_object.get_conclusion(),
            'Nouvelle licence ({})'.format(form.cleaned_data['license'])
        )

        # Update relationships in database
        publishable.sha_draft = sha
        publishable.save(force_slug_update=False)

        messages.success(self.request, EditContentLicense.success_message_license)

        # Update the preferred license of the user
        if form.cleaned_data['update_preferred_license']:
            profile = get_object_or_404(Profile, user=self.request.user)
            profile.licence = form.cleaned_data['license']
            profile.save()
            messages.success(self.request, EditContentLicense.success_message_profile_update)

        return redirect(form.previous_page_url)


class DeleteContent(LoginRequiredMixin, SingleContentViewMixin, DeleteView):
    model = PublishableContent
    template_name = None
    http_method_names = ['delete', 'post']
    object = None
    authorized_for_staff = False  # deletion is creator's privilege

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(DeleteContent, self).dispatch(*args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """rewrite delete() function to ensure repository deletion"""

        self.object = self.get_object()
        object_type = self.object.type.lower()

        _type = _('ce tutoriel')
        if self.object.is_article:
            _type = _('cet article')
        elif self.object.is_opinion:
            _type = _('ce billet')

        if self.object.authors.count() > 1:  # if more than one author, just remove author from list
            RemoveAuthorFromContent.remove_author(self.object, self.request.user)
            messages.success(self.request, _('Vous avez quitté la rédaction de {}.').format(_type))

        else:
            validation = Validation.objects.filter(content=self.object).order_by('-date_proposition').first()

            if validation and validation.status == 'PENDING_V':  # if the validation have a validator, warn him by PM
                if 'text' not in self.request.POST or len(self.request.POST['text'].strip()) < 3:
                    messages.error(self.request, _('Merci de fournir une raison à la suppression.'))
                    return redirect(self.object.get_absolute_url())
                else:
                    bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
                    msg = render_to_string(
                        'tutorialv2/messages/validation_cancel_on_delete.md',
                        {
                            'content': self.object,
                            'validator': validation.validator.username,
                            'user': self.request.user,
                            'message': '\n'.join(['> ' + line for line in self.request.POST['text'].split('\n')])
                        })
                    if not validation.content.validation_private_message:
                        validation.content.validation_private_message = send_mp(
                            bot,
                            [validation.validator],
                            _('Demande de validation annulée').format(),
                            self.object.title,
                            msg,
                            send_by_mail=False,
                            leave=True,
                            hat=get_hat_from_settings('validation'),
                            automatically_read=validation.validator
                        )
                        validation.content.save(force_slug_update=False)
                    else:
                        send_message_mp(
                            bot,
                            validation.content.validation_private_message,
                            msg,
                            hat=get_hat_from_settings('validation'),
                            no_notification_for=[self.request.user]
                        )
            if self.object.beta_topic is not None:
                beta_topic = self.object.beta_topic
                beta_topic.is_locked = True
                beta_topic.add_tags(['Supprimé'])
                beta_topic.save()
                post = beta_topic.first_post()
                post.update_content(
                    _('[[a]]\n'
                      '| Malheureusement, {} qui était en bêta a été supprimé par son auteur.\n\n').format(_type) +
                    post.text)

                post.save()

            self.object.delete()

            messages.success(self.request, _('Vous avez bien supprimé {}.').format(_type))

        return redirect(reverse(object_type + ':find-' + object_type, args=[request.user.username]))
