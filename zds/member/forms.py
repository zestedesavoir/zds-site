# coding: utf-8

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Fieldset, Submit, Field, \
    HTML, ButtonHolder, Reset

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from zds.member.models import Profile


class LoginForm(forms.Form):
    username = forms.CharField(
        label = 'Identifiant',
        max_length = 30,
        required = True,
    )

    password = forms.CharField(
        label = 'Mot magique',
        max_length = 76, 
        required = True,
        widget = forms.PasswordInput,
    )

    remember = forms.MultipleChoiceField(
        label = '',
        choices = (
            ('remember', "Connexion automatique"),
        ),
        initial = 'remember',
        widget = forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_action = reverse('zds.member.views.login_view')
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('username'),
            Field('password'),
            Field('remember'),
            HTML(u'<a href="{% url "zds.member.views.forgot_password" %}">Mot de passe oublié ?</a>'),
            ButtonHolder(
                Submit('submit', 'Se connecter'),
                HTML('<a class="btn btn-submit" href="/">Annuler</a>'),
                HTML('{% csrf_token %}'),
            ),
        )

class RegisterForm(forms.Form):
    email = forms.EmailField(
        label = 'Adresse e-mail',
        max_length = 100,
        required = True,
    )

    username = forms.CharField(
        label = 'Nom d\'utilisateur', 
        max_length = 30,
        required = True,
    )

    password = forms.CharField(
        label = 'Mot de passe', 
        max_length = 76,
        required = True,
        widget = forms.PasswordInput
    )

    password_confirm = forms.CharField(
        label = 'Confirmation', 
        max_length = 76,
        required = True,
        widget = forms.PasswordInput
    )

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('username'),
            Field('password'),
            Field('password_confirm'),
            Field('email'),
            ButtonHolder(
                Submit('submit', 'Valider mon inscription'),
                HTML('<a class="btn btn-submit" href="/">Annuler</a>'),
            )
        )

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()

        # Check that the password and it's confirmation match
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if not password_confirm == password:
            msg = u'Les mots de passe sont différents'
            self._errors['password'] = self.error_class([''])
            self._errors['password_confirm'] = self.error_class([msg])

            if 'password' in cleaned_data:
                del cleaned_data['password']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        # Check that the user doesn't exist yet
        username = cleaned_data.get('username')
        if User.objects.filter(username=username).count() > 0:
            msg = u'Ce nom d\'utilisateur est déjà utilisé'
            self._errors['username'] = self.error_class([msg])
            
        # Check that the email is unique
        email = cleaned_data.get('email')
        if User.objects.filter(email=email).count() > 0:
            msg = u'Votre email est déjà utilisée'
            self._errors['email'] = self.error_class([msg])
            
        return cleaned_data


# update extra information about user
class ProfileForm(forms.Form):
    biography = forms.CharField(
        label = 'Biographie',
        required = False,
        widget = forms.Textarea(
            attrs = {
                'placeholder': 'Votre biographie au format Markdown.'
            }
        )
    )

    site = forms.CharField(
        label = 'Site internet',
        required = False,
        max_length = 128,
        widget = forms.TextInput(
            attrs = {
                'placeholder': 'Lien vers votre site internet personnel (ne pas oublier le http:// ou https:// devant).'
            }
        )
    )
    
    avatar_url = forms.CharField(
        label = 'Avatar',
        required = False,
        widget = forms.TextInput(
            attrs = {
                'placeholder': 'Lien vers un avatar externe (laisser vide pour utiliser Gravatar).'
            }
        )
    )

    sign = forms.CharField(
        label = 'Signature',
        required = False,
        widget = forms.TextInput(
            attrs = {
                'placeholder': 'Elle apparaitra dans les messages de forums. '
            }
        )
    )

    options = forms.MultipleChoiceField(
        label = '',
        choices = (
            ('show_email', "Afficher mon adresse e-mail publiquement"),
            ('show_sign', "Afficher les signatures des autres membres"),
            ('hover_or_click', u"Dérouler les menus au survol de la souris ou au clic")
        ),
        widget = forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
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

        self.helper.layout = Layout(
            Field('biography'),
            Field('site'),
            Field('avatar_url'),
            Field('sign'),
            Field('options'),
            ButtonHolder(
                Submit('submit', 'Editer mon profil'),
                HTML('<a class="btn btn-submit" href="/">Annuler</a>'),
            )
        )

#to update email/username
class ChangeUserForm(forms.Form):
    
    username_new = forms.CharField(
        label = 'Nouveau pseudo',
        max_length = 30,
        required = False,
        widget = forms.TextInput(
            attrs = {
                'placeholder': 'Ne mettez rien pour conserver l\'ancien'
            }
        )
    )
    
    email_new = forms.EmailField(
        label = 'Nouvel e-mail',
        max_length = 100,
        required = False,
        widget = forms.TextInput(
            attrs = {
                'placeholder': 'Ne mettez rien pour conserver l\'ancien'
            }
        )
    )
    
    def __init__(self, *args, **kwargs):
        super(ChangeUserForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('username_new'),
            Field('email_new'),
            ButtonHolder(
                Submit('submit', 'Changer'),
                HTML('<a class="btn btn-submit" href="/">Annuler</a>'),
            ),
        )
        
# to update a password

class ChangePasswordForm(forms.Form):
    password_new = forms.CharField(
        label='Nouveau mot de passe', 
        max_length=76, 
        widget=forms.PasswordInput
    )

    password_old = forms.CharField(
        label='Mot de passe actuel',
        max_length=76,
        widget=forms.PasswordInput
    )

    password_confirm = forms.CharField(
        label='Confirmer le nouveau mot de passe',
        max_length=76,
        widget=forms.PasswordInput
    )

    def __init__(self, user, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.user = user

        self.helper.layout = Layout(
            Field('password_old'),
            Field('password_new'),
            Field('password_confirm'),
            ButtonHolder(
                Submit('submit', 'Changer'),
                HTML('<a class="btn btn-submit" href="/">Annuler</a>'),
            )
        )

    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()

        password_old = cleaned_data.get('password_old')
        password_new = cleaned_data.get('password_new')
        password_confirm = cleaned_data.get('password_confirm')

        # Check if the actual password is not empty
        if password_old:
            user_exist = authenticate(
                username=self.user.username, password=password_old
            )
            # Check if the user exist with old informations.
            if not user_exist and password_old != "":
                self._errors['password_old'] = self.error_class([u'Mot de passe incorrect.'])
                if 'password_old' in cleaned_data:
                    del cleaned_data['password_old']

        # Check that the password and it's confirmation match
        if not password_confirm == password_new:
            msg = u'Les mots de passe sont différents.'
            self._errors['password_new'] = self.error_class([msg])
            self._errors['password_confirm'] = self.error_class([msg])

            if 'password_new' in cleaned_data:
                del cleaned_data['password_new']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        return cleaned_data

# Reset the password

class ForgotPasswordForm(forms.Form):
    username = forms.CharField(
        label = 'Nom d\'utilisateur', 
        max_length = 30, 
        required = True
    )

    def __init__(self, *args, **kwargs):
        super(ForgotPasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('username'),
            ButtonHolder(
                Submit('submit', 'Envoyer'),
                HTML('<a class="btn btn-submit" href="/">Annuler</a>'),
            )
        )

class NewPasswordForm(forms.Form):
    password = forms.CharField(
        label='Mot de passe', 
        max_length=76, 
        widget=forms.PasswordInput
    )
    password_confirm = forms.CharField(
        label='Confirmation', 
        max_length=76, 
        widget=forms.PasswordInput
    )

    def __init__(self, *args, **kwargs):
        super(NewPasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-alone'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('password'),
            Field('password_confirm'),
            ButtonHolder(
                Submit('submit', 'Envoyer'),
                HTML('<a class="btn btn-submit" href="/">Annuler</a>'),
            )
        )

    def clean(self):
        cleaned_data = super(NewPasswordForm, self).clean()

        # Check that the password and it's confirmation match
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if not password_confirm == password:
            msg = u'Les mots de passe sont différents'
            self._errors['password'] = self.error_class([''])
            self._errors['password_confirm'] = self.error_class([msg])

            if 'password' in cleaned_data:
                del cleaned_data['password']

            if 'password_confirm' in cleaned_data:
                del cleaned_data['password_confirm']

        return cleaned_data
