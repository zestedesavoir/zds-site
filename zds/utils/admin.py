from django.contrib import admin

from zds.utils.models import Alert, Licence, Category, SubCategory, \
    CategorySubCategory, Tag, HelpWriting, CommentEdit


class SubCategoryAdmin(admin.ModelAdmin):

    def parent_category(self, obj):
        return obj.get_parent_category()

    parent_category.admin_order_field = 'categorysubcategory__category'
    parent_category.short_description = 'Parent category'

    list_display = ('parent_category', 'title', 'subtitle')
    ordering = ('categorysubcategory__category', 'title')


class AlertAdmin(admin.ModelAdmin):
    raw_id_fields = ('author', 'comment', 'moderator', 'privatetopic')


class CommentEditAdmin(admin.ModelAdmin):
    raw_id_fields = ('comment', 'editor', 'deleted_by')
    ordering = ('-date',)
    date_hierarchy = 'date'


admin.site.register(Alert, AlertAdmin)
admin.site.register(Tag)
admin.site.register(Licence)
admin.site.register(Category)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(CategorySubCategory)
admin.site.register(HelpWriting)
admin.site.register(CommentEdit, CommentEditAdmin)
