# coding: utf-8
import logging
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, FormView

from zds.member.decorator import LoginRequiredMixin, PermissionRequiredMixin, LoggedWithReadWriteHability
from zds.gallery.models import UserGallery
from zds.notification import signals
from zds.tutorialv2.forms import AskValidationForm, RejectValidationForm, AcceptValidationForm, RevokeValidationForm, \
    CancelValidationForm, PublicationForm, OpinionValidationForm, PromoteOpinionToArticleForm
from zds.tutorialv2.mixins import SingleContentFormViewMixin, SingleContentDetailViewMixin, ModalFormView, \
    SingleOnlineContentFormViewMixin
from zds.tutorialv2.models.models_database import Validation, PublishableContent
from zds.tutorialv2.publication_utils import publish_content, FailureDuringPublication, unpublish_content
from zds.tutorialv2.utils import init_new_repo
from zds.utils.forums import send_post, lock_topic
from zds.utils.models import SubCategory
from zds.utils.mps import send_mp


class ValidationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List the validations, with possibilities of filters"""

    permissions = ['tutorialv2.change_validation']
    context_object_name = 'validations'
    template_name = 'tutorialv2/validation/index.html'
    subcategory = None

    def get_queryset(self):

        # TODO: many filter at the same time ?
        # TODO: paginate ?

        queryset = Validation.objects\
            .prefetch_related('validator')\
            .prefetch_related('content')\
            .prefetch_related('content__authors')\
            .prefetch_related('content__subcategory')\
            .filter(Q(status='PENDING') | Q(status='PENDING_V'))

        # filtering by type
        try:
            type_ = self.request.GET['type']
            if type_ == 'orphan':
                queryset = queryset.filter(
                    validator__isnull=True,
                    status='PENDING')
            if type_ == 'reserved':
                queryset = queryset.filter(
                    validator__isnull=False,
                    status='PENDING_V')
            if type_ == 'article':
                queryset = queryset.filter(
                    content__type='ARTICLE')
            if type_ == 'tuto':
                queryset = queryset.filter(
                    content__type='TUTORIAL')
            else:
                raise KeyError()
        except KeyError:
            pass

        # filtering by category
        try:
            category_pk = int(self.request.GET['subcategory'])
            self.subcategory = get_object_or_404(SubCategory, pk=category_pk)
            queryset = queryset.filter(content__subcategory__in=[self.subcategory])
        except KeyError:
            pass
        except ValueError:
            raise Http404(u'Format invalide pour le paramètre de la sous-catégorie.')

        return queryset.order_by('date_proposition').all()

    def get_context_data(self, **kwargs):
        context = super(ValidationListView, self).get_context_data(**kwargs)
        removed_ids = []
        for validation in context['validations']:
            try:
                validation.versioned_content = validation.content.load_version(sha=validation.content.sha_validation)
            except IOError:  # remember that load_version can raise IOError when path is not correct
                logging.getLogger('zds.tutorialv2.validation')\
                       .warn('A validation {} for content {} failed to load'.format(validation.pk,
                                                                                    validation.content.title))
                removed_ids.append(validation.pk)
        context['validations'] = [_valid for _valid in context['validations'] if _valid.pk not in removed_ids]
        context['category'] = self.subcategory
        return context


class AskValidationForContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    """User ask validation for his tutorial. Staff member can also to that"""

    prefetch_all = False
    form_class = AskValidationForm
    must_be_author = True
    authorized_for_staff = True  # an admin could ask validation for a content
    only_draft_version = False
    modal_form = True

    def get_form_kwargs(self):
        # TODO : vérifier pour Mixin
        if not self.versioned_object.required_validation_before():
            raise PermissionDenied
        kwargs = super(AskValidationForContent, self).get_form_kwargs()
        kwargs['content'] = self.versioned_object
        return kwargs

    def form_valid(self, form):

        old_validation = Validation.objects.filter(
            content__pk=self.object.pk, status__in=['PENDING', 'PENDING_V']).first()

        if old_validation:  # if an old validation exists, cancel it !
            old_validator = old_validation.validator
            old_validation.status = 'CANCEL'
            old_validation.date_validation = datetime.now()
            old_validation.save()
        else:
            old_validator = None

        # create a 'validation' object
        validation = Validation()
        validation.content = self.object
        validation.date_proposition = datetime.now()
        validation.comment_authors = form.cleaned_data['text']
        validation.version = form.cleaned_data['version']
        if old_validator:
            validation.validator = old_validator
            validation.status = 'PENDING_V'
        validation.save()

        # warn the former validator that an update has been made, if any
        if old_validator:
            bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
            msg = render_to_string(
                'tutorialv2/messages/validation_change.md',
                {
                    'content': self.versioned_object,
                    'validator': validation.validator.username,
                    'url': self.versioned_object.get_absolute_url() + '?version=' + form.cleaned_data['version'],
                    'url_history': reverse('content:history', args=[self.object.pk, self.object.slug])
                })

            send_mp(
                bot,
                [old_validator],
                _(u'Une nouvelle version a été envoyée en validation.'),
                self.versioned_object.title,
                msg,
                False,
            )

        # update the content with the source and the version of the validation
        self.object.source = form.cleaned_data['source']
        self.object.sha_validation = validation.version
        self.object.save()

        messages.success(self.request, _(u"Votre demande de validation a été transmise à l'équipe."))

        self.success_url = self.versioned_object.get_absolute_url(version=self.sha)
        return super(AskValidationForContent, self).form_valid(form)


class CancelValidation(LoginRequiredMixin, ModalFormView):
    """The user or an admin cancel the validation process"""

    form_class = CancelValidationForm

    modal_form = True

    def get_form_kwargs(self):
        kwargs = super(CancelValidation, self).get_form_kwargs()
        kwargs['validation'] = Validation.objects.filter(pk=self.kwargs['pk']).last()
        return kwargs

    def form_valid(self, form):

        user = self.request.user

        validation = Validation.objects\
            .filter(pk=self.kwargs['pk'])\
            .prefetch_related('content')\
            .prefetch_related('content__authors')\
            .last()

        if not validation:
            raise PermissionDenied

        if validation.status not in ['PENDING', 'PENDING_V']:
            raise PermissionDenied  # cannot cancel a validation that is already accepted or rejected

        if user not in validation.content.authors.all() and not user.has_perm('tutorialv2.change_validation'):
            raise PermissionDenied

        versioned = validation.content.load_version(sha=validation.version)

        # reject validation:
        quote = '\n'.join(['> ' + line for line in form.cleaned_data['text'].split('\n')])
        validation.status = 'CANCEL'
        validation.comment_authors += _(u'\n\nLa validation a été **annulée** pour la raison suivante :\n\n{}')\
            .format(quote)
        validation.date_validation = datetime.now()
        validation.save()

        validation.content.sha_validation = None
        validation.content.save()

        # warn the former validator that the all thing have been canceled
        if validation.validator:
            bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
            msg = render_to_string(
                'tutorialv2/messages/validation_cancel.md',
                {
                    'content': versioned,
                    'validator': validation.validator.username,
                    'url': versioned.get_absolute_url() + '?version=' + validation.version,
                    'user': self.request.user,
                    'message': quote
                })

            send_mp(
                bot,
                [validation.validator],
                _(u'Demande de validation annulée').format(),
                versioned.title,
                msg,
                False,
            )

        messages.info(self.request, _(u'La validation de ce contenu a bien été annulée.'))

        self.success_url = reverse('content:view', args=[validation.content.pk, validation.content.slug]) + \
            '?version=' + validation.version

        return super(CancelValidation, self).form_valid(form)


class ReserveValidation(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Reserve or remove the reservation on a content"""

    permissions = ['tutorialv2.change_validation']

    def post(self, request, *args, **kwargs):
        validation = get_object_or_404(Validation, pk=kwargs['pk'])
        if validation.validator:
            validation.validator = None
            validation.date_reserve = None
            validation.status = 'PENDING'
            validation.save()
            messages.info(request, _(u"Ce contenu n'est plus réservé."))
            return redirect(reverse('validation:list'))
        else:
            validation.validator = request.user
            validation.date_reserve = datetime.now()
            validation.status = 'PENDING_V'
            validation.save()

            versioned = validation.content.load_version(sha=validation.version)
            msg = render_to_string(
                'tutorialv2/messages/validation_reserve.md',
                {
                    'content': versioned,
                    'url': versioned.get_absolute_url() + '?version=' + validation.version,
                })

            authors = list(validation.content.authors.all())
            if validation.validator in authors:
                authors.remove(validation.validator)
            if authors.__len__ > 0:
                send_mp(
                    validation.validator,
                    authors,
                    _(u'Contenu réservé - {0}').format(validation.content.title),
                    validation.content.title,
                    msg,
                    True,
                    leave=False,
                    direct=False,
                    mark_as_read=True
                )

            messages.info(request, _(u'Ce contenu a bien été réservé par {0}.').format(request.user.username))

            return redirect(
                reverse('content:view', args=[validation.content.pk, validation.content.slug]) +
                '?version=' + validation.version
            )


class HistoryOfValidationDisplay(LoginRequiredMixin, PermissionRequiredMixin, SingleContentDetailViewMixin):

    model = PublishableContent
    permissions = ['tutorialv2.change_validation']
    template_name = 'tutorialv2/validation/history.html'

    def get_context_data(self, **kwargs):
        context = super(HistoryOfValidationDisplay, self).get_context_data()

        context['validations'] = Validation.objects\
            .prefetch_related('validator')\
            .filter(content__pk=self.object.pk)\
            .order_by('date_proposition').all()

        return context


class RejectValidation(LoginRequiredMixin, PermissionRequiredMixin, ModalFormView):
    """Reject the publication"""

    permissions = ['tutorialv2.change_validation']
    form_class = RejectValidationForm

    modal_form = True

    def get_form_kwargs(self):
        kwargs = super(RejectValidation, self).get_form_kwargs()
        kwargs['validation'] = Validation.objects.filter(pk=self.kwargs['pk']).last()
        return kwargs

    def form_valid(self, form):

        user = self.request.user

        validation = Validation.objects.filter(pk=self.kwargs['pk']).last()

        if not validation:
            raise PermissionDenied

        if validation.validator != user:
            raise PermissionDenied

        if validation.status != 'PENDING_V':
            raise PermissionDenied

        # reject validation:
        validation.comment_validator = form.cleaned_data['text']
        validation.status = 'REJECT'
        validation.date_validation = datetime.now()
        validation.save()

        validation.content.sha_validation = None
        validation.content.save()

        # send PM
        versioned = validation.content.load_version(sha=validation.version)
        msg = render_to_string(
            'tutorialv2/messages/validation_reject.md',
            {
                'content': versioned,
                'url': versioned.get_absolute_url() + '?version=' + validation.version,
                'validator': validation.validator,
                'message_reject': '\n'.join(['> ' + a for a in form.cleaned_data['text'].split('\n')])
            })

        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        send_mp(
            bot,
            validation.content.authors.all(),
            _(u'Rejet de la demande de publication').format(),
            validation.content.title,
            msg,
            True,
            direct=False
        )

        messages.info(self.request, _(u'Le contenu a bien été refusé.'))
        self.success_url = reverse('validation:list')
        return super(RejectValidation, self).form_valid(form)


class AcceptValidation(LoginRequiredMixin, PermissionRequiredMixin, ModalFormView):
    """Publish the content"""

    permissions = ['tutorialv2.change_validation']
    form_class = AcceptValidationForm

    modal_form = True

    def get(self, request, *args, **kwargs):
        raise Http404(u"Publier un contenu depuis la validation n'est pas disponible en GET.")

    def get_form_kwargs(self):
        kwargs = super(AcceptValidation, self).get_form_kwargs()
        kwargs['validation'] = Validation.objects.filter(pk=self.kwargs['pk']).last()
        return kwargs

    def form_valid(self, form):

        user = self.request.user
        validation = Validation.objects.filter(pk=self.kwargs['pk']).last()

        if not validation:
            raise PermissionDenied

        if validation.validator != user:
            raise PermissionDenied

        if validation.status != 'PENDING_V':
            raise PermissionDenied

        # get database representation and validated version
        db_object = validation.content
        versioned = db_object.load_version(sha=validation.version)
        self.success_url = versioned.get_absolute_url(version=validation.version)
        is_update = db_object.sha_public
        try:
            published = publish_content(db_object, versioned, is_major_update=form.cleaned_data['is_major'])
        except FailureDuringPublication as e:
            messages.error(self.request, e.message)
        else:
            # save in database

            db_object.sha_public = validation.version
            db_object.source = form.cleaned_data['source']
            db_object.sha_validation = None

            db_object.public_version = published

            if form.cleaned_data['is_major'] or not is_update or db_object.pubdate is None:
                db_object.pubdate = datetime.now()
                db_object.is_obsolete = False

            # close beta if is an article
            if db_object.type == 'ARTICLE':
                db_object.sha_beta = None
                topic = db_object.beta_topic
                if topic is not None and not topic.is_locked:
                    msg_post = render_to_string(
                        'tutorialv2/messages/beta_desactivate.md', {'content': versioned}
                    )
                    send_post(self.request, topic, self.request.user, msg_post)
                    lock_topic(topic)

            db_object.save()

            # save validation object
            validation.comment_validator = form.cleaned_data['text']
            validation.status = 'ACCEPT'
            validation.date_validation = datetime.now()
            validation.save()

            # Follow
            signals.new_content.send(sender=db_object.__class__, instance=db_object, by_email=False)

            messages.success(self.request, _(u'Le contenu a bien été validé.'))
            self.success_url = published.get_absolute_url_online()

        return super(AcceptValidation, self).form_valid(form)


class RevokeValidation(LoginRequiredMixin, PermissionRequiredMixin, SingleOnlineContentFormViewMixin):
    """Unpublish a content and reverse the situation back to a pending validation"""

    permissions = ['tutorialv2.change_validation']
    form_class = RevokeValidationForm
    is_public = True

    modal_form = True

    def get_form_kwargs(self):
        kwargs = super(RevokeValidation, self).get_form_kwargs()
        kwargs['content'] = self.versioned_object
        return kwargs

    def form_valid(self, form):

        versioned = self.versioned_object

        if form.cleaned_data['version'] != self.object.sha_public:
            raise PermissionDenied

        validation = Validation.objects.filter(
            content=self.object,
            version=self.object.sha_public,
            status='ACCEPT').prefetch_related('content__authors').last()

        if not validation:
            raise PermissionDenied

        unpublish_content(self.object)

        validation.status = 'PENDING'
        validation.validator = None  # remove previous validator
        validation.date_validation = None
        validation.save()

        self.object.sha_public = None
        self.object.sha_validation = validation.version
        self.object.pubdate = None
        self.object.save()

        # send PM
        msg = render_to_string(
            'tutorialv2/messages/validation_revoke.md',
            {
                'content': versioned,
                'url': versioned.get_absolute_url() + '?version=' + validation.version,
                'admin': self.request.user,
                'message_reject': '\n'.join(['> ' + a for a in form.cleaned_data['text'].split('\n')])
            })

        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        send_mp(
            bot,
            validation.content.authors.all(),
            _(u'Dépublication'),
            validation.content.title,
            msg,
            True,
            direct=False
        )

        messages.success(self.request, _(u'Le contenu a bien été dépublié.'))
        self.success_url = self.versioned_object.get_absolute_url() + '?version=' + validation.version

        return super(RevokeValidation, self).form_valid(form)


class Publish(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    """Publish the content"""

    form_class = PublicationForm

    modal_form = True
    prefetch_all = False
    must_be_author = True
    authorized_for_staff = True  # an admin could ask validation for a content

    def get(self, request, *args, **kwargs):
        raise Http404(_(u"Publier un contenu n'est pas possible avec la méthode « GET »."))

    def get_form_kwargs(self):
        kwargs = super(Publish, self).get_form_kwargs()
        kwargs['content'] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        # get database representation and validated version
        db_object = self.object
        versioned = self.versioned_object
        self.success_url = versioned.get_absolute_url()
        is_update = db_object.sha_public
        try:
            published = publish_content(db_object, versioned, is_major_update=form.cleaned_data['is_major'])
        except FailureDuringPublication as e:
            messages.error(self.request, e.message)
        else:
            # save in database

            db_object.source = form.cleaned_data['source']
            db_object.sha_validation = None

            db_object.public_version = published

            if form.cleaned_data['is_major'] or not is_update or db_object.pubdate is None:
                db_object.pubdate = datetime.now()

            db_object.save()

            if is_update:
                msg = render_to_string(
                    'tutorialv2/messages/validation_accept_update.md',
                    {
                        'content': versioned,
                        'url': published.get_absolute_url_online(),
                        'validator': None
                    })
            else:
                msg = render_to_string(
                    'tutorialv2/messages/validation_accept_content.md',
                    {
                        'content': versioned,
                        'url': published.get_absolute_url_online(),
                        'validator': None
                    })

            bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
            send_mp(
                bot,
                db_object.authors.all(),
                _(u"Contenu publié"),
                versioned.title,
                msg,
                True,
                direct=False
            )

            messages.success(self.request, _(u'Le contenu a bien été publié.'))
            self.success_url = published.get_absolute_url_online()

        return super(Publish, self).form_valid(form)


class Unpublish(LoginRequiredMixin, SingleOnlineContentFormViewMixin):
    """Unpublish a content"""

    form_class = RevokeValidationForm
    is_public = True

    modal_form = True

    def get_form_kwargs(self):
        kwargs = super(Unpublish, self).get_form_kwargs()
        kwargs['content'] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        versioned = self.versioned_object

        user = self.request.user

        if user not in versioned.authors.all() and not user.has_perm('tutorialv2.change_validation'):
            raise PermissionDenied

        unpublish_content(self.object)

        self.object.sha_public = None
        self.object.pubdate = None
        self.object.save()

        # send PM
        msg = render_to_string(
            'tutorialv2/messages/validation_revoke.md',
            {
                'content': versioned,
                'url': versioned.get_absolute_url(),
                'admin': user,
                'message_reject': '\n'.join(['> ' + a for a in form.cleaned_data['text'].split('\n')])
            })

        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        send_mp(
            bot,
            versioned.authors.all(),
            _(u"Dépublication"),
            versioned.title,
            msg,
            True,
            direct=False
        )

        messages.success(self.request, _(u"Le contenu a bien été dépublié."))
        self.success_url = self.versioned_object.get_absolute_url()

        return super(Unpublish, self).form_valid(form)


class ValidPublication(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    """Publish the content"""

    form_class = OpinionValidationForm

    modal_form = True
    prefetch_all = False
    must_be_author = True
    authorized_for_staff = True

    def get(self, request, *args, **kwargs):
        raise Http404(_(u"Valider un contenu n'est pas possible avec la méthode « GET »."))

    def get_form_kwargs(self):
        kwargs = super(ValidPublication, self).get_form_kwargs()
        kwargs['content'] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        # get database representation and validated version
        db_object = self.object
        versioned = self.versioned_object
        self.success_url = versioned.get_absolute_url_online()

        db_object.sha_approved = form.cleaned_data['version']
        db_object.save()

        msg = render_to_string(
            'tutorialv2/messages/validation_opinion.md',
            {
                'title': versioned.title,
                'url': versioned.get_absolute_url(),
            })

        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        send_mp(
            bot,
            versioned.authors.all(),
            _(u"Billet approuvé"),
            versioned.title,
            msg,
            True,
            direct=False
        )

        messages.success(self.request, _(u'Le contenu a bien été validé.'))

        return super(ValidPublication, self).form_valid(form)



class MarkObsolete(LoginRequiredMixin, PermissionRequiredMixin, FormView):

    permissions = ['tutorialv2.change_validation']

    def get(self, request, *args, **kwargs):
        raise Http404(u"Marquer un contenu comme obsolète n'est pas disponible en GET.")

    def post(self, request, *args, **kwargs):
        content = get_object_or_404(PublishableContent, pk=kwargs['pk'])
        if not content.in_public():
            raise Http404
        if content.is_obsolete:
            content.is_obsolete = False
            messages.info(request, _(u"Le contenu n'est plus marqué comme obsolète."))
        else:
            content.is_obsolete = True
            messages.info(request, _(u'Le contenu est maintenant marqué comme obsolète.'))
        content.save()
        return redirect(content.get_absolute_url_online())


class PromoteOpinionToArticle(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    """Publish the content"""

    form_class = PromoteOpinionToArticleForm

    modal_form = True
    prefetch_all = False
    must_be_author = True
    authorized_for_staff = True

    def get(self, request, *args, **kwargs):
        raise Http404(_(u"Promouvoir un billet n'est pas possible avec la méthode « GET »."))

    def get_form_kwargs(self):
        kwargs = super(PromoteOpinionToArticle, self).get_form_kwargs()
        kwargs['content'] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        # get database representation and validated version
        db_object = self.object
        versioned = self.versioned_object

        # store data for later
        authors = db_object.authors.all()
        subcats = db_object.subcategory.all()
        tags = db_object.tags.all()
        gallery = db_object.gallery
        opinion_url = db_object.get_absolute_url_online()
        opinion = PublishableContent.objects.get(pk=db_object.pk)

        # copy object and update article to opinion
        # we set pk to None because next save will create a new object in database
        db_object.pk = None
        db_object.type = 'ARTICLE'
        db_object.creation_date = datetime.now()
        db_object.sha_public = None
        db_object.public_version = None
        db_object.save()

        # add information of the promotion on the original opinion
        opinion.promotion_content = db_object
        opinion.save()

        # add M2M objects
        for author in authors:
            db_object.authors.add(author)
        for subcat in subcats:
            db_object.subcategory.add(subcat)
        for tag in tags:
            db_object.tags.add(tag)

        # create the repo
        init_new_repo(db_object,
                      versioned.get_introduction(),
                      versioned.get_conclusion(),
                      u'Promotion du billet en article')

        # ask for validation
        validation = Validation()
        validation.content = db_object
        validation.date_proposition = datetime.now()
        validation.comment_authors = _(u'Promotion du billet « [{0}]({1}) » en article par [{2}]({3}).'.format(
            opinion.title,
            opinion.get_absolute_url_online(),
            self.request.user.username,
            self.request.user.profile.get_absolute_url()
        ))
        validation.version = db_object.sha_draft
        validation.save()
        db_object.sha_validation = validation.version

        # creating the gallery
        gal = gallery
        gal.pk = None
        gal.pubdate = datetime.now()
        gal.save()

        # creating relations between authors and gallery
        for author in authors:
            userg = UserGallery()
            userg.gallery = gal
            userg.mode = "W"  # write mode
            userg.user = author
            userg.save()
        db_object.gal = gal

        # save updates
        db_object.save()

        # send message to user
        msg = render_to_string(
            'tutorialv2/messages/opinion_promotion.md',
            {
                'content': versioned,
                'url': opinion_url,
            })

        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        send_mp(
            bot,
            db_object.authors.all(),
            _(u"Billet promu en article"),
            versioned.title,
            msg,
            True,
            direct=False
        )

        self.success_url = db_object.get_absolute_url()

        messages.success(self.request, _(u'Le billet a bien été promu en article et est en attente de validation.'))

        return super(PromoteOpinionToArticle, self).form_valid(form)
