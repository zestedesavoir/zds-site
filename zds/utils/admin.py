from django.contrib import admin

from zds.utils.models import Alert, Licence, Category


admin.site.register(Alert)
admin.site.register(Licence)
admin.site.register(Category)