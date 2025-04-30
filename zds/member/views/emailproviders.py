from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView

from zds.member.decorator import LoginRequiredMixin
from zds.member.forms import BannedEmailProviderForm
from zds.member.models import BannedEmailProvider, NewEmailProvider, Profile
from zds.utils.paginator import ZdSPagingListView


class NewEmailProvidersList(LoginRequiredMixin, PermissionRequiredMixin, ZdSPagingListView):
    permission_required = "member.change_bannedemailprovider"
    paginate_by = settings.ZDS_APP["member"]["providers_per_page"]

    model = NewEmailProvider
    context_object_name = "providers"
    template_name = "member/admin/new_email_providers.html"
    queryset = NewEmailProvider.objects.select_related("user").select_related("user__profile").order_by("-date")


@require_POST
@login_required
@permission_required("member.change_bannedemailprovider", raise_exception=True)
def check_new_email_provider(request, provider_pk):
    """Remove an alert about a new provider."""

    provider = get_object_or_404(NewEmailProvider, pk=provider_pk)
    if "ban" in request.POST and not BannedEmailProvider.objects.filter(provider=provider.provider).exists():
        BannedEmailProvider.objects.create(provider=provider.provider, moderator=request.user)
    provider.delete()

    messages.success(request, _("Action effectuée."))
    return redirect("new-email-providers")


class BannedEmailProvidersList(LoginRequiredMixin, PermissionRequiredMixin, ZdSPagingListView):
    """List the banned email providers."""

    permission_required = "member.change_bannedemailprovider"
    paginate_by = settings.ZDS_APP["member"]["providers_per_page"]

    model = BannedEmailProvider
    context_object_name = "providers"
    template_name = "member/admin/banned_email_providers.html"
    queryset = (
        BannedEmailProvider.objects.select_related("moderator").select_related("moderator__profile").order_by("-date")
    )


class MembersWithProviderList(LoginRequiredMixin, PermissionRequiredMixin, ZdSPagingListView):
    """List users using a banned email provider."""

    permission_required = "member.change_bannedemailprovider"
    paginate_by = settings.ZDS_APP["member"]["members_per_page"]

    model = User
    context_object_name = "members"
    template_name = "member/admin/members_with_provider.html"

    def get_object(self):
        return get_object_or_404(BannedEmailProvider, pk=self.kwargs["provider_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["provider"] = self.get_object()
        return context

    def get_queryset(self):
        provider = self.get_object()
        return (
            Profile.objects.select_related("user")
            .order_by("-last_visit")
            .filter(user__email__icontains=f"@{provider.provider}")
        )


class AddBannedEmailProvider(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Add an email provider to the banned list."""

    permission_required = "member.change_bannedemailprovider"

    model = BannedEmailProvider
    template_name = "member/admin/add_banned_email_provider.html"
    form_class = BannedEmailProviderForm
    success_url = reverse_lazy("banned-email-providers")

    def form_valid(self, form):
        form.instance.moderator = self.request.user
        messages.success(self.request, _("Le fournisseur a été banni."))
        return super().form_valid(form)


@require_POST
@login_required
@permission_required("member.change_bannedemailprovider", raise_exception=True)
def remove_banned_email_provider(request, provider_pk):
    """Unban an email provider."""

    provider = get_object_or_404(BannedEmailProvider, pk=provider_pk)
    provider.delete()

    messages.success(request, _("Le fournisseur « {} » a été débanni.").format(provider.provider))
    return redirect("banned-email-providers")
