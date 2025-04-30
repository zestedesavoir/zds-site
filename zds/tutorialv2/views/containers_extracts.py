import logging
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView, FormView

from zds.member.decorator import LoggedWithReadWriteHability
from zds.tutorialv2.forms import ContainerForm, ExtractForm, MoveElementForm
from zds.tutorialv2.mixins import (
    FormWithPreview,
    SingleContentFormViewMixin,
    SingleContentPostMixin,
    SingleContentViewMixin,
)
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.utils import (
    TooDeepContainerError,
    search_container_or_404,
    search_extract_or_404,
    try_adopt_new_child,
)
from zds.utils.misc import is_ajax

logger = logging.getLogger(__name__)


class CreateContainer(LoggedWithReadWriteHability, SingleContentFormViewMixin, FormWithPreview):
    template_name = "tutorialv2/create/container.html"
    form_class = ContainerForm
    content = None
    authorized_for_staff = True  # former behaviour

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["container"] = search_container_or_404(self.versioned_object, self.kwargs)
        context["gallery"] = self.object.gallery
        return context

    def render_to_response(self, context, **response_kwargs):
        parent = context["container"]
        if not parent.can_add_container():
            messages.error(self.request, _("Vous ne pouvez plus ajouter de conteneur à « {} ».").format(parent.title))
            return redirect(parent.get_absolute_url())

        return super().render_to_response(context, **response_kwargs)

    def form_valid(self, form):
        parent = search_container_or_404(self.versioned_object, self.kwargs)

        sha = parent.repo_add_container(
            form.cleaned_data["title"],
            form.cleaned_data["introduction"],
            form.cleaned_data["conclusion"],
            form.cleaned_data["msg_commit"],
        )

        # then save:
        self.object.sha_draft = sha
        self.object.update_date = datetime.now()
        self.object.save()

        self.success_url = parent.children[-1].get_absolute_url()

        return super().form_valid(form)


class EditContainer(LoggedWithReadWriteHability, SingleContentFormViewMixin, FormWithPreview):
    template_name = "tutorialv2/edit/container.html"
    form_class = ContainerForm
    content = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "preview" not in self.request.POST:
            container = search_container_or_404(self.versioned_object, self.kwargs)
            context["container"] = container
            context["gallery"] = self.object.gallery

        return context

    def get_initial(self):
        """rewrite function to pre-populate form"""
        initial = super().get_initial()
        container = search_container_or_404(self.versioned_object, self.kwargs)

        initial["title"] = container.title
        initial["introduction"] = container.get_introduction()
        initial["conclusion"] = container.get_conclusion()
        initial["container"] = container

        initial["last_hash"] = container.compute_hash()

        return initial

    def form_valid(self, form, *args, **kwargs):
        container = search_container_or_404(self.versioned_object, self.kwargs)

        # check if content has changed:
        current_hash = container.compute_hash()
        if current_hash != form.cleaned_data["last_hash"]:
            data = form.data.copy()
            data["last_hash"] = current_hash
            data["introduction"] = container.get_introduction()
            data["conclusion"] = container.get_conclusion()
            form.data = data
            messages.error(self.request, _("Une nouvelle version a été postée avant que vous ne validiez."))
            return self.form_invalid(form)

        sha = container.repo_update(
            form.cleaned_data["title"],
            form.cleaned_data["introduction"],
            form.cleaned_data["conclusion"],
            form.cleaned_data["msg_commit"],
            update_slug=self.object.public_version is None,
        )

        # then save
        self.object.sha_draft = sha
        self.object.update_date = datetime.now()
        self.object.save()

        self.success_url = container.get_absolute_url()

        return super().form_valid(form)


class CreateExtract(LoggedWithReadWriteHability, SingleContentFormViewMixin, FormWithPreview):
    template_name = "tutorialv2/create/extract.html"
    form_class = ExtractForm
    content = None
    authorized_for_staff = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["container"] = search_container_or_404(self.versioned_object, self.kwargs)
        context["gallery"] = self.object.gallery

        return context

    def render_to_response(self, context, **response_kwargs):
        parent = context["container"]
        if not parent.can_add_extract():
            messages.error(self.request, _("Vous ne pouvez plus ajouter de section à « {} ».").format(parent.title))
            return redirect(parent.get_absolute_url())

        return super().render_to_response(context, **response_kwargs)

    def form_valid(self, form):
        parent = search_container_or_404(self.versioned_object, self.kwargs)

        sha = parent.repo_add_extract(
            form.cleaned_data["title"], form.cleaned_data["text"], form.cleaned_data["msg_commit"]
        )

        # then save
        self.object.sha_draft = sha
        self.object.update_date = datetime.now()
        self.object.save()

        self.success_url = parent.children[-1].get_absolute_url()

        return super().form_valid(form)


class EditExtract(LoggedWithReadWriteHability, SingleContentFormViewMixin, FormWithPreview):
    template_name = "tutorialv2/edit/extract.html"
    form_class = ExtractForm
    content = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["gallery"] = self.object.gallery

        extract = search_extract_or_404(self.versioned_object, self.kwargs)
        context["extract"] = extract

        return context

    def get_initial(self):
        """rewrite function to pre-populate form"""
        initial = super().get_initial()
        extract = search_extract_or_404(self.versioned_object, self.kwargs)

        initial["title"] = extract.title
        initial["text"] = extract.get_text()
        initial["extract"] = extract

        initial["last_hash"] = extract.compute_hash()

        return initial

    def form_valid(self, form):
        extract = search_extract_or_404(self.versioned_object, self.kwargs)

        # check if content has changed:
        current_hash = extract.compute_hash()
        if current_hash != form.cleaned_data["last_hash"]:
            data = form.data.copy()
            data["last_hash"] = current_hash
            data["text"] = extract.get_text()
            form.data = data
            messages.error(self.request, _("Une nouvelle version a été postée avant que vous ne validiez."))
            return self.form_invalid(form)

        sha = extract.repo_update(
            form.cleaned_data["title"], form.cleaned_data["text"], form.cleaned_data["msg_commit"]
        )

        # then save
        self.object.update(sha_draft=sha, update_date=datetime.now())

        self.success_url = extract.get_absolute_url()
        if is_ajax(self.request):
            return JsonResponse(
                {"result": "ok", "last_hash": extract.compute_hash(), "new_url": extract.get_edit_url()}
            )
        return super().form_valid(form)


class DeleteContainerOrExtract(LoggedWithReadWriteHability, SingleContentViewMixin, DeleteView):
    model = PublishableContent
    template_name = None
    http_method_names = ["post"]
    object = None
    versioned_object = None

    def form_valid(self, form):
        """delete any object, either Extract or Container"""
        self.object = self.get_object()
        self.versioned_object = self.get_versioned_object()
        parent = search_container_or_404(self.versioned_object, self.kwargs)

        # find something to delete and delete it
        to_delete = None
        if "object_slug" in self.kwargs:
            try:
                to_delete = parent.children_dict[self.kwargs["object_slug"]]
            except KeyError:
                raise Http404("Impossible de récupérer le contenu pour le supprimer.")

        sha = to_delete.repo_delete()

        # then save
        self.object.update(sha_draft=sha, update_date=datetime.now())

        return redirect(parent.get_absolute_url())


class MoveChild(LoginRequiredMixin, SingleContentPostMixin, FormView):
    model = PublishableContent
    form_class = MoveElementForm
    versioned = False

    def get(self, request, *args, **kwargs):
        raise PermissionDenied

    def form_valid(self, form):
        content = self.get_object()
        versioned = content.load_version()
        base_container_slug = form.data["container_slug"]
        child_slug = form.data["child_slug"]

        if not base_container_slug:
            raise Http404("Le slug du container de base est vide.")

        if not child_slug:
            raise Http404("Le slug du container enfant est vide.")

        if base_container_slug == versioned.slug:
            parent = versioned
        else:
            search_params = {}

            if "first_level_slug" in form.data and form.data["first_level_slug"]:
                search_params["parent_container_slug"] = form.data["first_level_slug"]
                search_params["container_slug"] = base_container_slug
            else:
                search_params["container_slug"] = base_container_slug
            parent = search_container_or_404(versioned, search_params)

        try:
            child = parent.children_dict[child_slug]
            if form.data["moving_method"] == MoveElementForm.MOVE_UP:
                parent.move_child_up(child_slug)
                logger.debug(f"{child_slug} was moved up in tutorial id:{content.pk}")
            elif form.data["moving_method"] == MoveElementForm.MOVE_DOWN:
                parent.move_child_down(child_slug)
                logger.debug(f"{child_slug} was moved down in tutorial id:{content.pk}")
            elif form.data["moving_method"][0 : len(MoveElementForm.MOVE_AFTER)] == MoveElementForm.MOVE_AFTER:
                target = form.data["moving_method"][len(MoveElementForm.MOVE_AFTER) + 1 :]
                if not parent.has_child_with_path(target):
                    if "/" not in target:
                        target_parent = versioned
                    else:
                        target_parent = search_container_or_404(versioned, "/".join(target.split("/")[:-1]))

                        if target.split("/")[-1] not in target_parent.children_dict:
                            raise Http404("La cible n'est pas un enfant du parent.")
                    child = target_parent.children_dict[target.split("/")[-1]]
                    try_adopt_new_child(target_parent, parent.children_dict[child_slug])
                    # now, I will fix a bug that happens when the slug changes
                    # this one cost me so much of my hair
                    # and makes me think copy/past are killing kitty cat.
                    child_slug = target_parent.children[-1].slug
                    parent = target_parent
                parent.move_child_after(child_slug, target.split("/")[-1])
                logger.debug(f"{child_slug} was moved after {target} in tutorial id:{content.pk}")
            elif form.data["moving_method"][0 : len(MoveElementForm.MOVE_BEFORE)] == MoveElementForm.MOVE_BEFORE:
                target = form.data["moving_method"][len(MoveElementForm.MOVE_BEFORE) + 1 :]
                if not parent.has_child_with_path(target):
                    if "/" not in target:
                        target_parent = versioned
                    else:
                        target_parent = search_container_or_404(versioned, "/".join(target.split("/")[:-1]))

                        if target.split("/")[-1] not in target_parent.children_dict:
                            raise Http404("La cible n'est pas un enfant du parent.")
                    child = target_parent.children_dict[target.split("/")[-1]]
                    try_adopt_new_child(target_parent, parent.children_dict[child_slug])
                    # now, I will fix a bug that happens when the slug changes
                    # this one cost me so much of my hair
                    child_slug = target_parent.children[-1].slug
                    parent = target_parent
                parent.move_child_before(child_slug, target.split("/")[-1])
                logger.debug(f"{child_slug} was moved before {target} in tutorial id:{content.pk}")
            versioned.slug = content.slug  # we force not to change slug
            versioned.dump_json()
            parent.repo_update(
                parent.title,
                parent.get_introduction(),
                parent.get_conclusion(),
                _("Déplacement de ") + child_slug,
                update_slug=False,
            )
            content.sha_draft = versioned.sha_draft
            content.save()
            messages.info(self.request, _("L'élément a bien été déplacé."))
        except TooDeepContainerError:
            messages.error(
                self.request,
                _("Ce conteneur contient déjà trop d'enfants pour être" " inclus dans un autre conteneur."),
            )
        except KeyError:
            messages.warning(
                self.request,
                _(
                    "Vous n'avez pas complètement rempli le formulaire,"
                    "ou bien il est impossible de déplacer cet élément."
                ),
            )
        except ValueError as e:
            raise Http404("L'arbre spécifié n'est pas valide." + str(e))
        except IndexError:
            messages.warning(self.request, _("L'élément se situe déjà à la place souhaitée."))
            logger.debug(f"L'élément {child_slug} se situe déjà à la place souhaitée")
        except TypeError:
            messages.error(self.request, _("L'élément ne peut pas être déplacé à cet endroit."))
        if base_container_slug == versioned.slug:
            return redirect(reverse("content:view", args=[content.pk, content.slug]))
        else:
            return redirect(child.get_absolute_url())
