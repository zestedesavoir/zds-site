from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from zds.member.forms import PromoteMemberForm
from zds.member.models import Profile
from zds.member.utils import get_bot_account
from zds.mp.utils import send_mp
from zds.utils.models import get_hat_from_settings


@login_required
def settings_promote(request, user_pk):
    """
    Manage groups and activation status of a user.
    Only superusers are allowed to use this.
    """

    if not request.user.is_superuser:
        raise PermissionDenied

    profile = get_object_or_404(Profile, user__pk=user_pk)
    user = profile.user

    if request.method == "POST":
        form = PromoteMemberForm(request.POST)
        data = dict(form.data)

        groups = Group.objects.all()
        usergroups = user.groups.all()

        if "groups" in data:
            for group in groups:
                if str(group.id) in data["groups"]:
                    if group not in usergroups:
                        user.groups.add(group)
                        messages.success(
                            request, _("{0} appartient maintenant au groupe {1}.").format(user.username, group.name)
                        )
                else:
                    if group in usergroups:
                        user.groups.remove(group)
                        messages.warning(
                            request,
                            _("{0} n'appartient maintenant plus au groupe {1}.").format(user.username, group.name),
                        )
        else:
            user.groups.clear()
            messages.warning(request, _("{0} n'appartient (plus ?) à aucun groupe.").format(user.username))

        if "activation" in data and "on" in data["activation"]:
            user.is_active = True
            messages.success(request, _("{0} est maintenant activé.").format(user.username))
        else:
            user.is_active = False
            messages.warning(request, _("{0} est désactivé.").format(user.username))

        user.save()

        usergroups = user.groups.all()
        bot = get_bot_account()
        msg = _(
            "Bonjour {0},\n\n" "Un administrateur vient de modifier les groupes " "auxquels vous appartenez.  \n"
        ).format(user.username)
        if len(usergroups) > 0:
            msg = format_lazy("{}{}", msg, _("Voici la liste des groupes dont vous faites dorénavant partie :\n\n"))
            for group in usergroups:
                msg += f"* {group.name}\n"
        else:
            msg = format_lazy("{}{}", msg, _("* Vous ne faites partie d'aucun groupe"))
        send_mp(
            bot,
            [user],
            _("Modification des groupes"),
            "",
            msg,
            send_by_mail=True,
            leave=True,
            hat=get_hat_from_settings("moderation"),
        )

        return redirect(profile.get_absolute_url())

    form = PromoteMemberForm(initial={"groups": user.groups.all(), "activation": user.is_active})
    return render(request, "member/admin/promote.html", {"usr": user, "profile": profile, "form": form})
