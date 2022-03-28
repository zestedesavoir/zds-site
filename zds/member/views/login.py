from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.template.context_processors import csrf
from django.urls import reverse, resolve, Resolver404, NoReverseMatch
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.translation import gettext_lazy as _

from zds.member.forms import LoginForm
from zds.member.models import Profile
from zds.member.views import get_client_ip
from zds.utils.tokens import generate_token


def login_view(request):
    """Logs user in."""
    next_page = request.GET.get("next", "/")
    if next_page in [reverse("member-login"), reverse("register-member"), reverse("member-logout")]:
        next_page = "/"
    csrf_tk = {"next_page": next_page}
    csrf_tk.update(csrf(request))
    error = False

    if request.method != "POST":
        form = LoginForm()
    else:
        form = LoginForm(request.POST)

    if form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        user = User.objects.filter(username=username).first()
        if user is None:
            messages.error(
                request,
                _("Ce nom d’utilisateur est inconnu. Si vous ne possédez pas de compte, vous pouvez vous inscrire."),
            )
        else:
            if not user.is_active:
                messages.error(
                    request,
                    _(
                        "Vous n'avez pas encore activé votre compte, "
                        "vous devez le faire pour pouvoir vous "
                        "connecter sur le site. Regardez dans vos "
                        "mails : {}."
                    ).format(user.email),
                )
            else:
                user = authenticate(username=username, password=password)
                if user is None:
                    messages.error(
                        request,
                        _(
                            "Le mot de passe saisi est incorrect. Cliquez sur le lien « Mot de passe oublié ? »"
                            "si vous ne vous en souvenez plus."
                        ),
                    )
                    initial = {"username": username}

                    form = LoginForm(initial=initial)
                    form.helper.form_action += "?next=" + next_page
                    csrf_tk["error"] = error
                    csrf_tk["form"] = form
                    return render(request, "member/login.html", {"form": form, "csrf_tk": csrf_tk})
                else:
                    profile = get_object_or_404(Profile, user=user)
                    if not profile.can_read_now():
                        messages.error(
                            request,
                            _(
                                "Vous n'êtes pas autorisé à vous connecter sur le site, vous avez été banni par un "
                                "modérateur."
                            ),
                        )
                    else:
                        login(request, user)
                        request.session["get_token"] = generate_token()
                        if "remember" not in request.POST:
                            request.session.set_expiry(0)
                        profile.last_ip_address = get_client_ip(request)
                        profile.save()
                        # Redirect the user if needed.
                        # Set the cookie for Clem smileys.
                        # (For people switching account or clearing cookies
                        # after a browser session.)
                        try:
                            response = redirect(resolve(next_page).url_name)
                        except Resolver404:
                            response = redirect(reverse("homepage"))
                        return response

    form.helper.form_action += "?next=" + next_page
    csrf_tk["error"] = error
    csrf_tk["form"] = form
    return render(request, "member/login.html", {"form": form, "csrf_tk": csrf_tk, "next_page": next_page})
