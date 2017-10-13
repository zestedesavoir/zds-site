# coding: utf-8

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from captcha.fields import ReCaptchaField
from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout, \
    Submit, Field, ButtonHolder, Hidden, Div

from zds.member.models import Profile, KarmaNote, BannedEmailProvider
from zds.member.validators import validate_not_empty, validate_zds_email, validate_zds_username, validate_passwords, \
    validate_zds_password
from zds.utils.forms import CommonLayoutModalText
from zds.utils.misc import contains_utf8mb4
from zds.utils.models import Licence, HatRequest, Hat
from zds.utils import get_current_user

# Max password length for the user.
# Unlike other fields, this is not the length of DB field
MAX_PASSWORD_LENGTH = 76
# Min password length for the user.
MIN_PASSWORD_LENGTH = 6


class LoginForm(forms.Form):
    """
    The login form, including the "remember me" checkbox.
    """
    username = forms.CharField(
        label=_('Nom d\'utilisateur'),
        max_length=User._meta.get_field('username').max_length,
        required=True,
        widget=forms.TextInput(
            attrs={
                'autofocus': ''
            }
        ),
    )

    password = forms.CharField(
        label=_('Mot de passe'),
        max_length=MAX_PASSWORD_LENGTH,
        required=True,
        widget=forms.PasswordInput,
    )

    remember = forms.BooleanField(
        label=_('Se souvenir de moi'),
        initial=True,
        required=False,
    )

    def __init__(self, next=None, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('member-login')
        self.helper.form_method = 'post'
        self.helper.form_class = 'content-wrapper'

        self.helper.layout = Layout(
            Field('username'),
            Field('password'),
            Field('remember'),
            ButtonHolder(
                StrictButton(_('Se connecter'), type='submit'),
            )
        )


class RegisterForm(forms.Form):
    """
    Form to register a new user.
    """
    email = forms.EmailField(
        label=_('Adresse courriel'),
        max_length=User._meta.get_field('email').max_length,
        required=True,
        validators=[validate_not_empty, validate_zds_email],
    )

    username = forms.CharField(
        label=_('Nom d\'utilisateur'),
        max_length=User._meta.get_field('username').max_length,
        required=True,
        validators=[validate_not_empty, validate_zds_username],
    )

    password = forms.CharField(
        label=_('Mot de passe'),
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        required=True,
        widget=forms.PasswordInput,
        validators=[validate_zds_password],
    )

    password_confirm = forms.CharField(
        label=_('Confirmation du mot de passe'),
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        required=True,
        widget=forms.PasswordInput,
        validators=[validate_zds_password],
    )

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        layout = Layout(
            Field('username'),
            Field('password'),
            Field('password_confirm'),
            Field('email'),
        )

        # Add Captcha field if needed
        if settings.USE_CAPTCHA and settings.RECAPTCHA_PUBLIC_KEY != '' and settings.RECAPTCHA_PRIVATE_KEY != '':
            self.fields['captcha'] = ReCaptchaField()
            layout = Layout(
                layout,
                Field('captcha'),
            )

        layout = Layout(
            layout,
            ButtonHolder(
                Submit('submit', _('Valider mon inscription')),
            ))

        self.helper.layout = layout

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        return validate_passwords(cleaned_data)

    def throw_error(self, key=None, message=None):
        self._errors[key] = self.error_class([message])


class BannedEmailProviderForm(forms.ModelForm):
    class Meta:
        model = BannedEmailProvider
        fields = ('provider',)
        widgets = {
            'provider': forms.TextInput(attrs={
                'autofocus': 'on',
                'placeholder': _('Le nom de domaine à bannir.'),
            }),
        }

    def __init__(self, *args, **kwargs):
        super(BannedEmailProviderForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('provider'),
            ButtonHolder(
                StrictButton(_('Bannir ce fournisseur'), type='submit'),
            ))

    def clean_provider(self):
        data = self.cleaned_data['provider']
        return data.lower()


class ProfileModerationForm(forms.ModelForm):
    """
    Form used by moderators to update a user profile.
    """

    class Meta:
        model = Profile
        fields = ('biography', 'site', 'avatar_url', 'sign')
        widgets = {
            'biography': forms.Textarea(attrs={
                'placeholder': _("Modification de la biographie de l'utilisateur."),
                'class': 'md-editor'
            }),
            'sign': forms.TextInput(attrs={
                'placeholder': _('Modification de la signature.')
            }),
        }

    def __init__(self, *args, **kwargs):
        super(ProfileModerationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('biography'),
            Field('site'),
            Field('avatar_url'),
            Field('sign'),
            ButtonHolder(
                StrictButton(_('Enregistrer'), type='submit'),
            ))


class ProfileForm(forms.ModelForm):
    """
    Form used by users to update their profile.
    """

    class Meta:
        model = Profile
        fields = ('biography', 'site', 'avatar_url', 'sign', 'licence', 'show_sign', 'is_hover_enabled',
                  'allow_temp_visual_changes', 'use_old_smileys', 'show_markdown_help', 'email_for_answer')
        widgets = {
            'biography': forms.Textarea(attrs={
                'placeholder': _('Votre biographie au format Markdown.'),
                'class': 'md-editor preview-source'
            }),
            'site': forms.TextInput(attrs={
                'placeholder': _('Lien vers votre site web personnel (ne pas oublier le http:// ou https:// devant).'),
            }),
            'avatar_url': forms.TextInput(attrs={
                'placeholder': _('Lien vers un avatar externe (laissez vide pour utiliser Gravatar).')
            }),
            'sign': forms.TextInput(attrs={
                'placeholder': _('Elle apparaitra dans les messages de forums. ')
            })
        }

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)

        if not settings.ZDS_APP['member']['old_smileys_allowed']:
            del self.fields['use_old_smileys']

        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        layout = Layout(
            Field('biography'),
            ButtonHolder(StrictButton(_('Aperçu'), type='preview', name='preview',
                                      css_class='btn btn-grey preview-btn'),),
            HTML("""
                {% if form.biographie.value %}
                    {% include "misc/previsualization.part.html" with text=form.biographie.value %}
                {% endif %}
            """),
            Field('site'),
            Field('avatar_url'),
            HTML(_("""
                <p>
                    <a href="{% url 'gallery-list' %}">Choisir un avatar dans une galerie</a><br/>
                    Naviguez vers l'image voulue et cliquez sur le bouton "<em>Choisir comme avatar</em>".<br/>
                    Créez une galerie et importez votre avatar si ce n'est pas déjà fait !
                </p>
            """)),
            Field('sign'),
            Field('licence'),
            Field('show_sign'),
            Field('is_hover_enabled'),
            Field('allow_temp_visual_changes'),
            Field('show_markdown_help'),
            Field('email_for_answer'),
            ButtonHolder(
                StrictButton(_('Enregistrer'), type='submit'),
            ))

        if settings.ZDS_APP['member']['old_smileys_allowed']:
            layout.insert(13, 'use_old_smileys')

        self.helper.layout = layout


class GitHubTokenForm(forms.Form):
    """
    Updates the GitHub token.
    """
    github_token = forms.CharField(
        label='Token GitHub',
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': _('Token qui permet de communiquer avec la plateforme GitHub.'),
                'autocomplete': 'off'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(GitHubTokenForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('github_token'),
            ButtonHolder(
                StrictButton(_('Enregistrer'), type='submit'),
            ))


class ChangeUserForm(forms.Form):
    """
    Update username and email
    """
    username = forms.CharField(
        label=_('Mon pseudo'),
        max_length=User._meta.get_field('username').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': _('Pseudo')
            }
        ),
    )

    email = forms.EmailField(
        label=_('Mon adresse email'),
        max_length=User._meta.get_field('email').max_length,
        widget=forms.EmailInput(
            attrs={
                'placeholder': _('Adresse email')
            }
        ),
    )

    options = forms.MultipleChoiceField(
        label='',
        required=False,
        choices=(
            ('show_email', _('Afficher mon adresse courriel publiquement')),
        ),
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super(ChangeUserForm, self).__init__(*args, **kwargs)
        user = get_current_user()
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.previous_email = user.email
        self.previous_username = user.username
        self.fields['options'].initial = ''

        if user.profile.show_email:
            self.fields['options'].initial += 'show_email'

        self.helper.layout = Layout(
            Field('username', value=user.username),
            Field('email', value=user.email),
            Field('options'),
            ButtonHolder(
                StrictButton(_('Enregistrer'), type='submit'),
            ),
        )

    def clean(self):
        cleaned_data = super(ChangeUserForm, self).clean()
        cleaned_data['previous_username'] = self.previous_username
        cleaned_data['previous_email'] = self.previous_email
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        if username.lower() != self.previous_username.lower():
            validate_not_empty(username)
            validate_zds_username(username)
        if email != self.previous_email:
            validate_not_empty(email)
            validate_zds_email(email)
        return cleaned_data


# TODO: Updates the password --> requires a better name
class ChangePasswordForm(forms.Form):

    password_old = forms.CharField(
        label=_('Mot de passe actuel (si défini)'),
        widget=forms.PasswordInput,
        required=False,
    )

    password_new = forms.CharField(
        label=_('Nouveau mot de passe'),
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput,
        validators=[validate_zds_password],
    )

    password_confirm = forms.CharField(
        label=_('Confirmer le nouveau mot de passe'),
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput,
        validators=[validate_zds_password],
    )

    def __init__(self, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('password_old'),
            Field('password_new'),
            Field('password_confirm'),
            ButtonHolder(
                StrictButton(_('Enregistrer'), type='submit'),
            )
        )

    def clean_password_old(self):
        old_password = self.cleaned_data.get('password_old')
        if get_current_user().has_usable_password() and not get_current_user().check_password(old_password):
            raise forms.ValidationError(_('Vous avez un mot de passe défini et votre saisie est incorrecte.'))
        if not get_current_user().has_usable_password() and old_password:
            raise forms.ValidationError(_("Aucun mot de passe n'est associé à votre compte."))

    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()
        return validate_passwords(cleaned_data, password_label='password_new',
                                  username=get_current_user().username)


class UsernameAndEmailForm(forms.Form):
    username = forms.CharField(
        label=_('Nom d\'utilisateur'),
        required=False,
    )

    email = forms.CharField(
        label=_('Adresse de courriel'),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(UsernameAndEmailForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Div(
                Field('username'),
                ButtonHolder(
                    StrictButton(_('Envoyer'), type='submit'),
                ),
                css_id='form-username'
            ),
            Div(
                Field('email'),
                ButtonHolder(
                    StrictButton(_('Envoyer'), type='submit'),
                ),
                css_id='form-email'
            )
        )

    def clean(self):
        cleaned_data = super(UsernameAndEmailForm, self).clean()

        # Clean data
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')

        if username and email:
            self._errors['username'] = self.error_class([_('Seul un des deux champ doit être rempli. Remplissez soi'
                                                           't l\'adresse de courriel soit le nom d\'utilisateur')])
        elif not username and not email:
            self._errors['username'] = self.error_class([_('Il vous faut remplir au moins un des deux champs')])
        else:
            # run validators
            if username:
                validate_not_empty(username)
                validate_zds_username(username, check_username_available=False)
            else:
                validate_not_empty(email)
                validate_zds_email(email, check_username_available=False)

        return cleaned_data


class NewPasswordForm(forms.Form):
    """
    Defines a new password (when the current one has been forgotten)
    """
    password = forms.CharField(
        label=_('Mot de passe'),
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput,
        validators=[validate_zds_password],
    )
    password_confirm = forms.CharField(
        label=_('Confirmation'),
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput,
        validators=[validate_zds_password],
    )

    def __init__(self, identifier, *args, **kwargs):
        super(NewPasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.username = identifier

        self.helper.layout = Layout(
            Field('password'),
            Field('password_confirm'),
            ButtonHolder(
                StrictButton(_('Envoyer'), type='submit'),
            )
        )

    def clean(self):
        cleaned_data = super(NewPasswordForm, self).clean()
        return validate_passwords(cleaned_data, username=self.username)


class PromoteMemberForm(forms.Form):
    """
    Promotes a user to an arbitrary group
    """
    groups = forms.ModelMultipleChoiceField(
        label=_('Groupe de l\'utilisateur'),
        queryset=Group.objects.all(),
        required=False,
    )

    activation = forms.BooleanField(
        label=_('Compte actif'),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(PromoteMemberForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('groups'),
            Field('activation'),
            StrictButton(_('Valider'), type='submit'),
        )


class KarmaForm(forms.Form):
    note = forms.CharField(
        label=_('Commentaire'),
        max_length=KarmaNote._meta.get_field('note').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': _('Commentaire sur le comportement de ce membre'),
                'required': 'required'
            }),
        required=True,
    )

    karma = forms.IntegerField(
        max_value=100,
        min_value=-100,
        initial=0,
        required=False,
    )

    def __init__(self, profile, *args, **kwargs):
        super(KarmaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('member-modify-karma')
        self.helper.form_class = 'modal modal-flex'
        self.helper.form_id = 'karmatiser-modal'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutModalText(),
            Field('note'),
            Field('karma'),
            Hidden('profile_pk', '{{ profile.pk }}'),
            ButtonHolder(
                StrictButton('Valider', type='submit'),
            ),
        )


class BannedEmailProviderForm(forms.ModelForm):
    class Meta:
        model = BannedEmailProvider
        fields = ('provider',)
        widgets = {
            'provider': forms.TextInput(attrs={
                'autofocus': 'on',
                'placeholder': _('Le nom de domaine à bannir.'),
            }),
        }

    def __init__(self, *args, **kwargs):
        super(BannedEmailProviderForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('provider'),
            ButtonHolder(
                StrictButton(_('Bannir ce fournisseur'), type='submit'),
            ))

    def clean_provider(self):
        data = self.cleaned_data['provider']
        return data.lower()


class HatRequestForm(forms.ModelForm):
    class Meta:
        model = HatRequest
        fields = ('hat', 'reason')
        widgets = {
            'hat': forms.TextInput(attrs={
                'placeholder': _('La casquette que vous demandez.'),
            }),
            'reason': forms.Textarea(attrs={
                'placeholder': _('Expliquez pourquoi vous devriez porter cette casquette (3000 caractères maximum).'),
            }),
        }

    def __init__(self, *args, **kwargs):
        super(HatRequestForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.helper.form_action = '{}#send-request'.format(reverse('hats-settings'))

        self.helper.layout = Layout(
            Field('hat'),
            Field('reason'),
            ButtonHolder(
                StrictButton(_('Envoyer la demande'), type='submit'),
            ))

    def clean_hat(self):
        data = self.cleaned_data['hat']
        user = get_current_user()
        if contains_utf8mb4(data):
            raise forms.ValidationError(_('Les caractères utf8mb4 ne sont pas autorisés dans les casquettes.'))
        if data.lower() in [hat.name.lower() for hat in user.profile.get_hats()]:
            raise forms.ValidationError(_('Vous possédez déjà cette casquette.'))
        if data.lower() in [hat.lower() for hat in user.requested_hats.values_list('hat', flat=True)]:
            raise forms.ValidationError(_('Vous avez déjà demandé cette casquette.'))
        try:
            hat = Hat.objects.get(name__iexact=data)
            if hat.group:
                raise forms.ValidationError(_('Cette casquette n\'est accordée qu\'aux membres '
                                              'd\'un groupe particulier. Vous ne pouvez pas '
                                              'la demander.'))
        except Hat.DoesNotExist:
            pass
        return data
