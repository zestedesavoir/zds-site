from collections import OrderedDict, defaultdict

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, TemplateView

from zds.forum.models import Forum
from zds.notification.models import NewPublicationSubscription
from zds.tutorialv2.mixins import ContentTypeMixin
from zds.tutorialv2.models import CONTENT_TYPE_LIST, TYPE_CHOICES_DICT
from zds.tutorialv2.models.database import ContentReaction, PublishableContent, PublishedContent
from zds.utils.models import Category, CategorySubCategory, SubCategory, Tag
from zds.utils.paginator import ZdSPagingListView, make_pagination
from zds.utils.templatetags.topbar import topbar_publication_categories
from zds.utils.uuslug_wrapper import slugify


class ListOnlineContents(ContentTypeMixin, ZdSPagingListView):
    """Displays the list of published contents"""

    context_object_name = "public_contents"
    paginate_by = settings.ZDS_APP["content"]["content_per_page"]
    template_name = "tutorialv2/index_online_contents.html"
    category = None
    subcategory = None
    tag = None
    current_content_type = None

    def get_queryset(self):
        """Filter the contents to obtain the list of contents of given type.
        If category parameter is provided, only contents which have this category will be listed.
        :return: list of contents with the right type
        :rtype: list of zds.tutorialv2.models.database.PublishedContent
        """
        sub_query = "SELECT COUNT(*) FROM {} WHERE {}={} AND {}={} AND utils_comment.is_visible=1".format(
            "tutorialv2_contentreaction,utils_comment",
            "tutorialv2_contentreaction.related_content_id",
            "tutorialv2_publishablecontent.id",
            "utils_comment.id",
            "tutorialv2_contentreaction.comment_ptr_id",
        )
        queryset = PublishedContent.objects.filter(must_redirect=False)
        # this condition got more complexe with development of zep13
        # if we do filter by content_type, then every published content can be
        # displayed. Othewise, we have to be sure the content was expressly chosen by
        # someone with staff authorization. Another way to say it "it has to be a
        # validated content (article, tutorial), `ContentWithoutValidation` live their
        # own life in their own page.
        if self.current_content_type:
            queryset = queryset.filter(content_type=self.current_content_type)
        else:
            queryset = queryset.filter(~Q(content_type="OPINION"))
        # prefetch:
        queryset = (
            queryset.prefetch_related("content")
            .prefetch_related("content__subcategory")
            .prefetch_related("content__authors")
            .prefetch_related("content__tags")
            .select_related("content__licence")
            .select_related("content__image")
            .select_related("content__last_note")
            .select_related("content__last_note__related_content")
            .select_related("content__last_note__related_content__public_version")
            .filter(pk=F("content__public_version__pk"))
        )

        if "category" in self.request.GET:
            self.subcategory = get_object_or_404(SubCategory, slug=self.request.GET.get("category"))
            queryset = queryset.filter(content__subcategory__in=[self.subcategory])

        if "tag" in self.request.GET:
            self.tag = get_object_or_404(Tag, slug=slugify(self.request.GET.get("tag").lower().strip()))
            # TODO: fix me
            # different tags can have same slug such as C/C#/C++, as a first version we get all of them
            queryset = queryset.filter(content__tags__in=[self.tag])
        queryset = queryset.extra(select={"count_note": sub_query})
        return queryset.order_by("-publication_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for public_content in context["public_contents"]:
            if public_content.content.last_note is not None:
                public_content.content.last_note.related_content = public_content.content
                public_content.content.public_version = public_content
                public_content.content.count_note = public_content.count_note

        context["category"] = self.category
        context["subcategory"] = self.subcategory
        context["tag"] = self.tag
        context["topbar_publication_categories"] = topbar_publication_categories(self.current_content_type)

        return context


class ListOpinions(ListOnlineContents):
    """Displays the list of published opinions"""

    current_content_type = "OPINION"


class ViewPublications(TemplateView):
    templates = {
        1: "tutorialv2/view/categories.html",
        2: "tutorialv2/view/category.html",
        3: "tutorialv2/view/subcategory.html",
        4: "tutorialv2/view/browse.html",
    }
    handle_types = ["TUTORIAL", "ARTICLE"]

    level = 1
    max_last_contents = settings.ZDS_APP["content"]["max_last_publications_level_1"]
    template_name = templates[level]

    @staticmethod
    def categories_with_contents_count(handle_types):
        """Select categories with subcategories and contents count in two queries"""

        queryset_category = (
            Category.objects.order_by("position")
            .filter(categorysubcategory__subcategory__publishablecontent__publishedcontent__must_redirect=False)
            .filter(categorysubcategory__subcategory__publishablecontent__type__in=handle_types)
            .annotate(
                contents_count=Count(
                    "categorysubcategory__subcategory__publishablecontent__publishedcontent", distinct=True
                )
            )
            .distinct()
        )

        queryset_subcategory = (
            CategorySubCategory.objects.prefetch_related("subcategory", "category")
            .filter(is_main=True)
            .order_by("category__id", "subcategory__title")
            .annotate(sub_contents_count=Count("subcategory__publishablecontent__publishedcontent", distinct=True))
            .all()
        )

        subcategories_sorted = defaultdict(list)
        for category_to_sub_category in queryset_subcategory:
            if category_to_sub_category.sub_contents_count:
                subcategories_sorted[category_to_sub_category.category.id].append(category_to_sub_category.subcategory)

        categories = queryset_category
        for category in categories:
            category.subcategories = subcategories_sorted[category.id]

        return categories

    @staticmethod
    def subcategories_with_contents_count(category, handle_types):
        """Rewritten to give the number of contents at the same time as the subcategories (in one query)"""

        # TODO: check if we can use ORM to do that
        sub_query = """
          SELECT COUNT(*) FROM `tutorialv2_publishedcontent`
          INNER JOIN `tutorialv2_publishablecontent`
            ON (`tutorialv2_publishedcontent`.`content_id` = `tutorialv2_publishablecontent`.`id`)
          INNER JOIN `tutorialv2_publishablecontent_subcategory`
            ON (`tutorialv2_publishablecontent`.`id` =
              `tutorialv2_publishablecontent_subcategory`.`publishablecontent_id`)
          WHERE (
            `tutorialv2_publishedcontent`.`must_redirect` = 0
            AND `tutorialv2_publishablecontent`.`type` IN ({})
            AND `tutorialv2_publishablecontent_subcategory`.`subcategory_id` =
              `utils_categorysubcategory`.`subcategory_id`)
        """.format(
            ", ".join(f"'{t}'" for t in handle_types)
        )

        queryset = (
            CategorySubCategory.objects.filter(is_main=True, category=category)
            .prefetch_related("subcategory")
            .order_by("subcategory__title")
            .extra(select={"contents_count": sub_query})
        )

        subcategories = []

        for category_to_subcategory in queryset:
            subcategory = category_to_subcategory.subcategory
            subcategory.contents_count = category_to_subcategory.contents_count
            subcategories.append(subcategory)

        return subcategories

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.kwargs.get("slug", False):
            self.level = 2
            self.max_last_contents = settings.ZDS_APP["content"]["max_last_publications_level_2"]
        if self.kwargs.get("slug_category", False):
            self.level = 3
            self.max_last_contents = settings.ZDS_APP["content"]["max_last_publications_level_3"]
        if (
            self.request.GET.get("category", False)
            or self.request.GET.get("subcategory", False)
            or self.request.GET.get("type", False)
            or self.request.GET.get("tag", False)
        ):
            self.level = 4
            self.max_last_contents = 50

        self.template_name = self.templates[self.level]
        recent_kwargs = {}

        if self.level == 1:
            # get categories and subcategories
            categories = ViewPublications.categories_with_contents_count(self.handle_types)

            context["categories"] = categories
            context["content_count"] = PublishedContent.objects.last_contents(
                content_type=self.handle_types, with_comments_count=False
            ).count()

        elif self.level == 2:
            context["category"] = get_object_or_404(Category, slug=self.kwargs.get("slug"))
            context["subcategories"] = ViewPublications.subcategories_with_contents_count(
                context["category"], self.handle_types
            )
            recent_kwargs["subcategories"] = context["subcategories"]

        elif self.level == 3:
            subcategory = get_object_or_404(SubCategory, slug=self.kwargs.get("slug"))
            context["category"] = subcategory.get_parent_category()

            if context["category"].slug != self.kwargs.get("slug_category"):
                raise Http404(
                    "wrong slug for category ({} != {})".format(
                        context["category"].slug, self.kwargs.get("slug_category")
                    )
                )

            context["subcategory"] = subcategory
            recent_kwargs["subcategories"] = [subcategory]

        elif self.level == 4:
            category = self.request.GET.get("category", None)
            subcategory = self.request.GET.get("subcategory", None)
            subcategories = None
            if category is not None:
                context["category"] = get_object_or_404(Category, slug=category)
                subcategories = context["category"].get_subcategories()
            elif subcategory is not None:
                subcategory = get_object_or_404(SubCategory, slug=self.request.GET.get("subcategory"))
                context["category"] = subcategory.get_parent_category()
                context["subcategory"] = subcategory
                subcategories = [subcategory]

            content_type = self.handle_types
            context["type"] = None
            if "type" in self.request.GET:
                _type = self.request.GET.get("type", "").upper()
                if _type in self.handle_types:
                    content_type = _type
                    context["type"] = TYPE_CHOICES_DICT[_type]
                else:
                    raise Http404(f"wrong type {_type}")

            tag = self.request.GET.get("tag", None)
            tags = None
            if tag is not None:
                tags = [get_object_or_404(Tag, slug=slugify(tag))]
                context["tag"] = tags[0]

            contents_queryset = PublishedContent.objects.last_contents(
                subcategories=subcategories, tags=tags, content_type=content_type
            )
            items_per_page = settings.ZDS_APP["content"]["content_per_page"]
            make_pagination(
                context,
                self.request,
                contents_queryset,
                items_per_page,
                context_list_name="filtered_contents",
                with_previous_item=False,
            )

        if self.level < 4:
            last_articles = PublishedContent.objects.last_contents(**dict(content_type="ARTICLE", **recent_kwargs))
            context["last_articles"] = last_articles[: self.max_last_contents]
            context["more_articles"] = last_articles.count() > self.max_last_contents

            last_tutorials = PublishedContent.objects.last_contents(**dict(content_type="TUTORIAL", **recent_kwargs))
            context["last_tutorials"] = last_tutorials[: self.max_last_contents]
            context["more_tutorials"] = last_tutorials.count() > self.max_last_contents

            context["beta_forum"] = (
                Forum.objects.prefetch_related("category").filter(pk=settings.ZDS_APP["forum"]["beta_forum_id"]).last()
            )

        context["level"] = self.level
        return context


class TagsListView(ListView):
    model = Tag
    template_name = "tutorialv2/view/tags.html"
    context_object_name = "tags"
    displayed_types = ["TUTORIAL", "ARTICLE"]

    def get_queryset(self):
        if "type" in self.request.GET:
            t = self.request.GET.get("type").upper()
            if t not in CONTENT_TYPE_LIST:
                raise Http404(f"type {t} unknown")
            self.displayed_types = [t]

        return PublishedContent.objects.get_top_tags(self.displayed_types)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["tags_to_display"] = "publications"

        if len(self.displayed_types) == 1:
            context["tags_to_display"] = self.displayed_types[0]

        return context


class ContentOfAuthor(ZdSPagingListView):
    type = "ALL"
    context_object_name = "contents"
    paginate_by = settings.ZDS_APP["content"]["content_per_page"]
    template_name = "tutorialv2/index.html"
    model = PublishableContent

    authorized_filters = OrderedDict(
        [
            ("public", [lambda p, t: p.get_user_public_contents_queryset(t), _("Publiés"), True, "tick green"]),
            ("validation", [lambda p, t: p.get_user_validate_contents_queryset(t), _("En validation"), False, "tick"]),
            ("beta", [lambda p, t: p.get_user_beta_contents_queryset(t), _("En bêta"), True, "beta"]),
            ("redaction", [lambda p, t: p.get_user_draft_contents_queryset(t), _("Brouillons"), False, "edit"]),
        ]
    )
    sorts = OrderedDict(
        [
            ("creation", [lambda q: q.order_by("creation_date"), _("Par date de création")]),
            ("abc", [lambda q: q.order_by("title"), _("Par ordre alphabétique")]),
            ("modification", [lambda q: q.order_by("-update_date"), _("Par date de dernière modification")]),
        ]
    )
    sort = ""
    filter = ""
    user = None

    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, username=self.kwargs["username"])
        if self.user != self.request.user and "filter" in self.request.GET:
            filter_ = self.request.GET.get("filter").lower()
            if filter_ in self.authorized_filters:
                if not self.authorized_filters[filter_][2]:
                    raise PermissionDenied
            else:
                raise Http404("Le filtre n'est pas autorisé.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        profile = self.user.profile
        if self.type == "ALL":
            _type = None
        elif self.type in list(TYPE_CHOICES_DICT.keys()):
            _type = self.type
        else:
            raise Http404("Ce type de contenu est inconnu dans le système.")

        # Filter.
        if "filter" in self.request.GET:
            self.filter = self.request.GET["filter"].lower()
            if self.filter not in self.authorized_filters:
                raise Http404("Le filtre n'est pas autorisé.")
        elif self.user != self.request.user:
            self.filter = "public"

        if self.filter == "":
            queryset = profile.get_user_contents_queryset(_type=_type)
        else:
            queryset = self.authorized_filters[self.filter][0](profile, _type)
        # prefetch:
        queryset = (
            queryset.prefetch_related("authors")
            .prefetch_related("subcategory")
            .select_related("licence")
            .select_related("image")
        )

        # Sort.
        if "sort" in self.request.GET and self.request.GET["sort"].lower() in self.sorts:
            self.sort = self.request.GET["sort"]
        elif not self.sort:
            self.sort = "modification"
        queryset = self.sorts[self.sort.lower()][0](queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sorts"] = []
        context["filters"] = []
        context["sort"] = self.sort.lower()
        context["filter"] = self.filter.lower()
        context["subscriber_count"] = NewPublicationSubscription.objects.get_subscriptions(self.user).count()
        context["type"] = self.type.lower()

        if self.type == "ALL":
            contents = list(context["contents"])
            context["tutorials"] = [content for content in contents if content.type == "TUTORIAL"]
            context["articles"] = [content for content in contents if content.type == "ARTICLE"]
            context["opinions"] = [content for content in contents if content.type == "OPINION"]

        context["usr"] = self.user
        for sort in list(self.sorts.keys()):
            context["sorts"].append({"key": sort, "text": self.sorts[sort][1]})
        for filter_ in list(self.authorized_filters.keys()):
            authorized_filter = self.authorized_filters[filter_]
            if self.user != self.request.user and not authorized_filter[2]:
                continue
            context["filters"].append({"key": filter_, "text": authorized_filter[1], "icon": authorized_filter[3]})
        return context


class ListContentReactions(ZdSPagingListView):
    context_object_name = "content_reactions"
    template_name = "tutorialv2/comment/list.html"
    paginate_by = settings.ZDS_APP["forum"]["posts_per_page"]
    model = ContentReaction
    user = None

    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return ContentReaction.objects.get_all_messages_of_a_user(self.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "usr": self.user,
                "hidden_content_reactions_count": ContentReaction.objects.filter(author=self.user).distinct().count()
                - context["paginator"].count,
            }
        )

        return context
