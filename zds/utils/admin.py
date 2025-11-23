from django.contrib import admin

from zds.utils.models import (
    Alert,
    Category,
    CategorySubCategory,
    CommentEdit,
    Hat,
    HatRequest,
    Licence,
    SubCategory,
    Tag,
)


class SubCategoryAdmin(admin.ModelAdmin):
    def parent_category(self, obj):
        return obj.get_parent_category()

    parent_category.admin_order_field = "categorysubcategory__category"
    parent_category.short_description = "Parent category"

    list_display = ("parent_category", "title", "subtitle", "position")
    ordering = ("categorysubcategory__category", "position", "title")


class AlertAdmin(admin.ModelAdmin):
    list_display = ("author", "scope", "text", "pubdate", "solved", "solved_date")
    list_filter = ("scope", "solved")
    raw_id_fields = ("author", "comment", "moderator", "privatetopic", "profile", "content")
    ordering = ("-pubdate",)
    search_fields = ("author__username", "text")


class CommentEditAdmin(admin.ModelAdmin):
    list_display = ("editor", "date")
    raw_id_fields = ("comment", "editor", "deleted_by")
    ordering = ("-date",)
    date_hierarchy = "date"
    search_fields = ("editor__username", "original_text")


class HatAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "is_staff")
    list_filter = ("group", "is_staff")
    search_fields = ("name",)


class HatRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "hat", "date")
    ordering = ("-date",)
    raw_id_fields = ("user",)
    search_fields = ("user__username", "hat")


admin.site.register(Alert, AlertAdmin)
admin.site.register(Tag)
admin.site.register(Licence)
admin.site.register(Category)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(CategorySubCategory)
admin.site.register(CommentEdit, CommentEditAdmin)
admin.site.register(Hat, HatAdmin)
admin.site.register(HatRequest, HatRequestAdmin)
