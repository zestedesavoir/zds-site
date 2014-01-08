from django.contrib import admin

from zds.utils.models import Alert, Licence, Category, SubCategory, CategorySubCategory


admin.site.register(Alert)
admin.site.register(Licence)
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(CategorySubCategory)