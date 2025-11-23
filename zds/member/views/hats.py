from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView

from zds.member.decorator import LoginRequiredMixin
from zds.member.forms import HatRequestForm
from zds.pages.models import GroupContact
from zds.utils.misc import is_ajax
from zds.utils.models import Hat, HatRequest, get_hat_to_add
from zds.utils.paginator import ZdSPagingListView


class HatsList(ZdSPagingListView):
    """Display the list of hats."""

    context_object_name = "hats"
    paginate_by = settings.ZDS_APP["member"]["hats_per_page"]
    template_name = "member/hats.html"
    queryset = (
        Hat.objects.order_by("name")
        .select_related("group")
        .prefetch_related("group__user_set")
        .prefetch_related("group__user_set__profile")
        .prefetch_related("profile_set")
        .prefetch_related("profile_set__user")
    )


class HatDetail(DetailView):
    model = Hat
    context_object_name = "hat"
    template_name = "member/hat.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hat = context["hat"]
        if self.request.user.is_authenticated:
            context["is_required"] = HatRequest.objects.filter(
                user=self.request.user, hat__iexact=hat.name, is_granted__isnull=True
            ).exists()
        if hat.group:
            context["users"] = hat.group.user_set.select_related("profile")
            try:
                context["groupcontact"] = hat.group.groupcontact
            except GroupContact.DoesNotExist:
                context["groupcontact"] = None  # group not displayed on contact page
        else:
            context["users"] = [p.user for p in hat.profile_set.select_related("user")]
        return context


class HatsSettings(LoginRequiredMixin, CreateView):
    model = HatRequest
    template_name = "member/settings/hats.html"
    form_class = HatRequestForm

    def get_initial(self):
        initial = super().get_initial()
        if "ask" in self.request.GET:
            try:
                hat = Hat.objects.get(pk=int(self.request.GET["ask"]))
                initial["hat"] = hat.name
            except (ValueError, Hat.DoesNotExist):
                pass
        return initial

    def post(self, request, *args, **kwargs):
        if "preview" in request.POST and is_ajax(request):
            content = render(request, "misc/preview.part.html", {"text": request.POST.get("text")})
            return StreamingHttpResponse(content)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, _("Votre demande a bien été envoyée."))
        return super().form_valid(form)

    def get_success_url(self):
        # To remove #send-request HTML-anchor.
        return "{}#".format(reverse("hats-settings"))


class RequestedHatsList(LoginRequiredMixin, PermissionRequiredMixin, ZdSPagingListView):
    permission_required = "utils.change_hat"
    paginate_by = settings.ZDS_APP["member"]["requested_hats_per_page"]

    model = HatRequest
    context_object_name = "requests"
    template_name = "member/admin/requested_hats.html"
    queryset = (
        HatRequest.objects.filter(is_granted__isnull=True)
        .select_related("user")
        .select_related("user__profile")
        .order_by("-date")
    )


class SolvedHatRequestsList(LoginRequiredMixin, PermissionRequiredMixin, ZdSPagingListView):
    permission_required = "utils.change_hat"
    paginate_by = settings.ZDS_APP["member"]["requested_hats_per_page"]

    model = HatRequest
    context_object_name = "requests"
    template_name = "member/admin/solved_hat_requests.html"
    queryset = (
        HatRequest.objects.filter(is_granted__isnull=False)
        .select_related("user")
        .select_related("user__profile")
        .select_related("moderator")
        .select_related("moderator__profile")
        .order_by("-solved_at")
    )


class HatRequestDetail(LoginRequiredMixin, DetailView):
    model = HatRequest
    context_object_name = "hat_request"
    template_name = "member/admin/hat_request.html"

    def get_object(self, queryset=None):
        request = super().get_object()
        if request.user != self.request.user and not self.request.user.has_perm("utils.change_hat"):
            raise PermissionDenied
        return request


@require_POST
@login_required
@permission_required("utils.change_hat", raise_exception=True)
@transaction.atomic
def solve_hat_request(request, request_pk):
    """
    Solve a hat request by granting or denying the requested hat
    according to moderator's decision.
    """

    hat_request = get_object_or_404(HatRequest, pk=request_pk)

    if hat_request.is_granted is not None:
        raise PermissionDenied

    try:
        hat_request.solve(
            "grant" in request.POST, request.user, request.POST.get("comment", ""), request.POST.get("hat", None)
        )
        messages.success(request, _("La demande a été résolue."))
        return redirect("requested-hats")
    except ValueError as e:
        messages.error(request, str(e))
        return redirect(hat_request.get_absolute_url())


@require_POST
@login_required
@permission_required("utils.change_hat", raise_exception=True)
@transaction.atomic
def add_hat(request, user_pk):
    """
    Add a hat to a user.
    Creates the hat if it doesn't exist.
    """

    user = get_object_or_404(User, pk=user_pk)

    hat_name = request.POST.get("hat", "")

    try:
        hat = get_hat_to_add(hat_name, user)
        user.profile.hats.add(hat)
        try:  # if hat was requested, remove the relevant request
            hat_request = HatRequest.objects.get(user=user, hat__iexact=hat.name, is_granted__isnull=True)
            hat_request.solve(
                is_granted=False,
                comment=_(
                    "La demande a été automatiquement annulée car " "la casquette vous a été accordée manuellement."
                ),
            )
        except HatRequest.DoesNotExist:
            pass
        messages.success(request, _("La casquette a bien été ajoutée."))
    except ValueError as e:
        messages.error(request, str(e))

    return redirect(user.profile.get_absolute_url())


@require_POST
@login_required
@transaction.atomic
def remove_hat(request, user_pk, hat_pk):
    """Remove a hat from a user."""

    user = get_object_or_404(User, pk=user_pk)
    hat = get_object_or_404(Hat, pk=hat_pk)
    if user != request.user and not request.user.has_perm("utils.change_hat"):
        raise PermissionDenied
    if hat not in user.profile.hats.all():
        raise Http404

    user.profile.hats.remove(hat)

    messages.success(request, _("La casquette a bien été retirée."))
    return redirect(user.profile.get_absolute_url())
