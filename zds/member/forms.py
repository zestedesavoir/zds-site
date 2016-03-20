# coding: utf-8

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from captcha.fields import ReCaptchaField
from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout, \
    Submit, Field, ButtonHolder, Hidden, Div

from zds.member.models import Profile, listing, KarmaNote
from zds.member.validators import ProfileUsernameValidator, ProfileEmailValidator
from zds.utils.forms import CommonLayoutModalText

# Max password length for the user.
# Unlike other fields, this is not the length of DB field
MAX_PASSWORD_LENGTH = 76
# Min password length for the user.
MIN_PASSWORD_LENGTH = 6


class OldTutoForm(forms.Form):
    """
    This form to attributes "Old" tutorials to the current user.
    """
    id = forms.ChoiceField(
        label=_(u'Ancien Tutoriel'),
        required=True,
        choices=listing(),
    )

    def __init__(self, profile, *args, **kwargs):
        super(OldTutoForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'modal modal-flex'
        self.helper.form_id = 'link-tuto-modal'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('member-add-oldtuto')

        self.helper.layout = Layout(
            HTML(_(u'<p>Choisissez un tutoriel du SdZ à attribuer au membre</p>')),
            Field('id'),
            Hidden('profile_pk', '{{ profile.pk }}'),
            ButtonHolder(
                StrictButton(_(u'Attribuer'), type='submit'),
            ),
        )


class LoginForm(forms.Form):
    """
    The login form, including the "remember me" checkbox.
    """
    username = forms.CharField(
        label=_(u"Nom d'utilisateur"),
        max_length=User._meta.get_field('username').max_length,
        required=True,
        widget=forms.TextInput(
            attrs={
                'autofocus': ''
            }
        )
    )

    password = forms.CharField(
        label=_(u'Mot de passe'),
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        required=True,
        widget=forms.PasswordInput,
    )

    remember = forms.BooleanField(
        label=_(u'Se souvenir de moi'),
        initial=True,
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
            HTML('{% csrf_token %}'),
            ButtonHolder(
                StrictButton(_(u'Se connecter'), type='submit'),
            )
        )


class RegisterForm(forms.Form, ProfileUsernameValidator, ProfileEmailValidator):
    """
    Form to register a new user.
    """
    email = forms.EmailField(
        label=_(u'Adresse courriel'),
        max_length=User._meta.get_field('email').max_length,
        required=True,
    )

    username = forms.CharField(
        label=_(u'Nom d\'utilisateur'),
        max_length=User._meta.get_field('username').max_length,
        required=True,
    )

    password = forms.CharField(
        label=_(u'Mot de passe'),
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        required=True,
        widget=forms.PasswordInput
    )

    password_confirm = forms.CharField(
        label=_(u'Confirmation du mot de passe'),
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        required=True,
        widget=forms.PasswordInput
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
                Submit('submit', _(u'Valider mon inscription')),
            ))

        self.helper.layout = layout

    def clean(self):
        """
        Cleans the input data and performs following checks:
        - Both passwords are the same
        - Username doesn't exist in database
        - Username is not empty
        - Username doesn't contain any comma (this will break the personal message system)
        - Username doesn't begin or ends with spaces
        - Password is different of username
        - Email address is unique through all users
        - Email provider is not a forbidden one
        Forbidden email providers are stored in `forbidden_email_providers.txt` on project root.
        :return: Cleaned data, and the error messages if they exist.
        """
        cleaned_data = super(RegisterForm, self).clean()

        # Check that the password and it's confirmation match
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if not password_confirm == password:
            msg = _(u'Les mots de passe sont différents')
            self._errors['password'] = self.error_class([msg])
            self._errors['password_confirm'] = self.error_class([msg])

            if 'password' in cleaned_data:
                del cleaned_data['password']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        # Check that the user doesn't exist yet
        username = cleaned_data.get('username')
        self.validate_username(username)

        if username is not None:
            # Check that password != username
            if password == username:
                msg = _(u'Le mot de passe doit être différent du pseudo')
                self._errors['password'] = self.error_class([msg])
                if 'password' in cleaned_data:
                    del cleaned_data['password']
                if 'password_confirm' in cleaned_data:
                    del cleaned_data['password_confirm']

        email = cleaned_data.get('email')
        self.validate_email(email)

        return cleaned_data

    def throw_error(self, key=None, message=None):
        self._errors[key] = self.error_class([message])


class MiniProfileForm(forms.Form):
    """
    Updates some profile data: biography, website, avatar URL, signature.
    """
    biography = forms.CharField(
        label=_('Biographie'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre biographie au format Markdown.'),
                'class': 'md-editor'
            }
        )
    )

    site = forms.CharField(
        label='Site internet',
        required=False,
        max_length=Profile._meta.get_field('site').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Lien vers votre site internet '
                                 u'personnel (ne pas oublier le http:// ou https:// devant).')
            }
        )
    )

    avatar_url = forms.CharField(
        label='Avatar',
        required=False,
        max_length=Profile._meta.get_field('avatar_url').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Lien vers un avatar externe '
                                 u'(laissez vide pour utiliser Gravatar).')
            }
        )
    )

    sign = forms.CharField(
        label='Signature',
        required=False,
        max_length=Profile._meta.get_field('sign').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Elle apparaitra dans les messages de forums. ')
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(MiniProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('biography'),
            Field('site'),
            Field('avatar_url'),
            Field('sign'),
            ButtonHolder(
                StrictButton(_(u'Enregistrer'), type='submit'),
            ))


class ProfileForm(MiniProfileForm):
    """
    Updates main profile rules:
    - Display email address to everybody
    - Display signatures
    - Display menus on hover
    - Receive an email when receiving a personal message
    """
    options = forms.MultipleChoiceField(
        label='',
        required=False,
        choices=(
            ('show_email', _(u"Afficher mon adresse courriel publiquement")),
            ('show_sign', _(u"Afficher les signatures")),
            ('hover_or_click', _(u"Cochez pour dérouler les menus au survol")),
            ('allow_temp_visual_changes', _(u"Activer les changements visuels temporaires")),
            ('zds_smileys', _(u"Active le pack de smileys Clem")),
            ('email_for_answer', _(u'Recevez un courriel lorsque vous recevez une réponse à un message privé')),
        ),
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        # to get initial value form checkbox show email
        initial = kwargs.get('initial', {})
        self.fields['options'].initial = ''

        if 'show_email' in initial and initial['show_email']:
            self.fields['options'].initial += 'show_email'

        if 'show_sign' in initial and initial['show_sign']:
            self.fields['options'].initial += 'show_sign'

        if 'hover_or_click' in initial and initial['hover_or_click']:
            self.fields['options'].initial += 'hover_or_click'

        if 'allow_temp_visual_changes' in initial and initial['allow_temp_visual_changes']:
            self.fields['options'].initial += 'allow_temp_visual_changes'

        if 'zds_smileys' in initial and initial['zds_smileys']:
            self.fields['options'].initial += 'zds_smileys'

        if 'email_for_answer' in initial and initial['email_for_answer']:
            self.fields['options'].initial += 'email_for_answer'

        self.helper.layout = Layout(
            Field('biography'),
            Field('site'),
            Field('avatar_url'),
            HTML(u"""
                <p><a href="{% url 'gallery-list' %}">Choisir un avatar dans une galerie</a><br/>
                   Naviguez vers l'image voulue et cliquez sur le bouton "<em>Choisir comme avatar</em>".<br/>
                   Créez une galerie et importez votre avatar si ce n'est pas déjà fait !</p>
            """),
            Field('sign'),
            Field('options'),
            ButtonHolder(
                StrictButton(_(u'Enregistrer'), type='submit'),
            ))


class ChangeUserForm(forms.Form, ProfileUsernameValidator, ProfileEmailValidator):
    """
    Update username and email
    """
    username = forms.CharField(
        label=_(u'Nouveau pseudo'),
        max_length=User._meta.get_field('username').max_length,
        min_length=1,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Ne mettez rien pour conserver l\'ancien')
            }
        ),
    )

    email = forms.EmailField(
        label=_(u'Nouvelle adresse courriel'),
        max_length=User._meta.get_field('email').max_length,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Ne mettez rien pour conserver l\'ancien')
            }
        ),
        error_messages={'invalid': _(u'Veuillez entrer une adresse email valide.'), }
    )

    def __init__(self, *args, **kwargs):
        super(ChangeUserForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('username'),
            Field('email'),
            ButtonHolder(
                StrictButton(_(u'Enregistrer'), type='submit'),
            ),
        )

    def clean(self):
        cleaned_data = super(ChangeUserForm, self).clean()

        username_new = cleaned_data.get('username')
        if username_new is not None:
            self.validate_username(username_new)

        email_new = cleaned_data.get('email')
        if email_new is not None:
            self.validate_email(email_new)

        return cleaned_data

    def throw_error(self, key=None, message=None):
        self._errors[key] = self.error_class([message])


# TODO: Updates the password --> requires a better name
class ChangePasswordForm(forms.Form):

    password_new = forms.CharField(
        label=_(u'Nouveau mot de passe'),
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput,
    )

    password_old = forms.CharField(
        label=_(u'Mot de passe actuel'),
        widget=forms.PasswordInput,
    )

    password_confirm = forms.CharField(
        label=_(u'Confirmer le nouveau mot de passe'),
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput,
    )

    def __init__(self, user, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.user = user

        self.helper.layout = Layout(
            Field('password_old'),
            Field('password_new'),
            Field('password_confirm'),
            ButtonHolder(
                StrictButton(_(u'Enregistrer'), type='submit'),
            )
        )

    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()

        password_old = cleaned_data.get('password_old')
        password_new = cleaned_data.get('password_new')
        password_confirm = cleaned_data.get('password_confirm')

        # TODO: mutualizes these rules with registration ones?
        # Check if the actual password is not empty
        if password_old:
            user_exist = authenticate(
                username=self.user.username, password=password_old
            )
            # Check if the user exist with old informations.
            if not user_exist and password_old != "":
                self._errors['password_old'] = self.error_class(
                    [_(u'Mot de passe incorrect.')])
                if 'password_old' in cleaned_data:
                    del cleaned_data['password_old']

        # Check that the password and it's confirmation match
        if not password_confirm == password_new:
            msg = _(u'Les mots de passe sont différents.')
            self._errors['password_new'] = self.error_class([msg])
            self._errors['password_confirm'] = self.error_class([msg])

            if 'password_new' in cleaned_data:
                del cleaned_data['password_new']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        # Check that password != username
        if password_new == self.user.username:
            msg = _(u'Le mot de passe doit être différent de votre pseudo')
            self._errors['password_new'] = self.error_class([msg])
            if 'password_new' in cleaned_data:
                del cleaned_data['password_new']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        return cleaned_data


class UsernameAndEmailForm(forms.Form):
    username = forms.CharField(
        label=_(u'Nom d\'utilisateur'),
        required=False
    )

    email = forms.CharField(
        label=_(u'Adresse de courriel'),
        required=False
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
                    StrictButton(_(u'Envoyer'), type='submit'),
                ),
                css_id='form-username'
            ),
            Div(
                Field('email'),
                ButtonHolder(
                    StrictButton(_(u'Envoyer'), type='submit'),
                ),
                css_id='form-email'
            )
        )

    def clean(self):
        cleaned_data = super(UsernameAndEmailForm, self).clean()

        # Clean data
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')

        # Check that the username or the email is filled
        if (username and email) or (not username and not email):
            if username and email:
                self._errors['username'] = self.error_class([_(u'Les deux champs ne doivent pas être rempli. '
                                                               u'Remplissez soit l\'adresse de courriel soit le '
                                                               u'nom d\'utilisateur')])
            else:
                self._errors['username'] = self.error_class([_(u'Il vous faut remplir au moins un des deux champs')])
        else:
            # Check if the user exist
            if username:
                if User.objects.filter(Q(username=username)).count() == 0:
                    self._errors['username'] = self.error_class([_(u'Ce nom d\'utilisateur n\'existe pas')])

            if email:
                if User.objects.filter(Q(email=email)).count() == 0:
                    self._errors['email'] = self.error_class([_(u'Cette adresse de courriel n\'existe pas')])

        return cleaned_data


class NewPasswordForm(forms.Form):
    """
    Defines a new password (when the current one has been forgotten)
    """
    password = forms.CharField(
        label=_(u'Mot de passe'),
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput
    )
    password_confirm = forms.CharField(
        label=_(u'Confirmation'),
        max_length=MAX_PASSWORD_LENGTH,
        min_length=MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput
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
                StrictButton(_(u'Envoyer'), type='submit'),
            )
        )

    def clean(self):
        cleaned_data = super(NewPasswordForm, self).clean()

        # Check that the password and it's confirmation match
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        # TODO: mutualizes these rules with registration ones?
        if not password_confirm == password:
            msg = _(u'Les mots de passe sont différents')
            self._errors['password'] = self.error_class([''])
            self._errors['password_confirm'] = self.error_class([msg])

            if 'password' in cleaned_data:
                del cleaned_data['password']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        # Check that password != username
        if password == self.username:
            msg = _(u'Le mot de passe doit être différent de votre pseudo')
            self._errors['password'] = self.error_class([msg])
            if 'password' in cleaned_data:
                del cleaned_data['password']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        return cleaned_data


class PromoteMemberForm(forms.Form):
    """
    Promotes a user to an arbitrary group
    """
    groups = forms.ModelMultipleChoiceField(
        label=_(u"Groupe de l'utilisateur"),
        queryset=Group.objects.all(),
        required=False,
    )

    superuser = forms.BooleanField(
        label=_(u"Super-user"),
        required=False,
    )

    activation = forms.BooleanField(
        label=_(u"Compte actif"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(PromoteMemberForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('groups'),
            Field('superuser'),
            Field('activation'),
            StrictButton(_(u'Valider'), type='submit'),
        )


class KarmaForm(forms.Form):
    warning = forms.CharField(
        label=_(u"Commentaire"),
        max_length=KarmaNote._meta.get_field('comment').max_length,
        widget=forms.TextInput(
            attrs={
                'placeholder': u'Commentaire sur le comportement de ce membre'
            }),
        required=True,
    )

    points = forms.IntegerField(
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
            Field('warning'),
            Field('points'),
            Hidden('profile_pk', '{{ profile.pk }}'),
            ButtonHolder(
                StrictButton(u'Valider', type='submit'),
            ),
        )
