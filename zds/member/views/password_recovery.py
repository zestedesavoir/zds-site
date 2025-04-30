import uuid
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.member.forms import NewPasswordForm, UsernameAndEmailForm
from zds.member.models import TokenForgotPassword


def forgot_password(request):
    """If the user has forgotten his password, they can get a new one."""

    if request.method == "POST":
        form = UsernameAndEmailForm(request.POST)
        if form.is_valid():
            # Get data from form
            data = form.data
            username = data["username"]
            email = data["email"]

            # Fetch the user, we need his email address
            usr = None
            if username:
                usr = get_object_or_404(User, Q(username=username))

            if email:
                usr = get_object_or_404(User, Q(email=email))

            # Generate a valid token during one hour
            uuid_token = str(uuid.uuid4())
            date_end = datetime.now() + timedelta(days=0, hours=1, minutes=0, seconds=0)
            token = TokenForgotPassword(user=usr, token=uuid_token, date_end=date_end)
            token.save()

            # Send email
            subject = _("{} - Mot de passe oublié").format(settings.ZDS_APP["site"]["literal_name"])
            from_email = "{} <{}>".format(
                settings.ZDS_APP["site"]["literal_name"], settings.ZDS_APP["site"]["email_noreply"]
            )
            context = {
                "username": usr.username,
                "site_name": settings.ZDS_APP["site"]["literal_name"],
                "site_url": settings.ZDS_APP["site"]["url"],
                "url": settings.ZDS_APP["site"]["url"] + token.get_absolute_url(),
            }
            message_html = render_to_string("email/member/confirm_forgot_password.html", context)
            message_txt = render_to_string("email/member/confirm_forgot_password.txt", context)

            msg = EmailMultiAlternatives(subject, message_txt, from_email, [usr.email])
            msg.attach_alternative(message_html, "text/html")
            msg.send()
            return render(request, "member/forgot_password/success.html")
        else:
            return render(request, "member/forgot_password/index.html", {"form": form})
    form = UsernameAndEmailForm()
    return render(request, "member/forgot_password/index.html", {"form": form})


def new_password(request):
    """Create a new password for a user."""

    try:
        token = request.GET["token"]
    except KeyError:
        return redirect(reverse("homepage"))
    token = get_object_or_404(TokenForgotPassword, token=token)
    if request.method == "POST":
        form = NewPasswordForm(token.user.username, request.POST)
        if form.is_valid():
            data = form.data
            password = data["password"]
            # User can't confirm his request if it is too late

            if datetime.now() > token.date_end:
                return render(request, "member/new_password/failed.html")
            token.user.set_password(password)
            token.user.save()
            token.delete()
            return render(request, "member/new_password/success.html")
        else:
            return render(request, "member/new_password/index.html", {"form": form})
    form = NewPasswordForm(identifier=token.user.username)
    return render(request, "member/new_password/index.html", {"form": form})
