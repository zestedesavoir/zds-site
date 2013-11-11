from django.contrib import admin
from lbp.utils.models import DateManager, Alert, Licence, Category, Version
 
admin.site.register(DateManager)
admin.site.register(Alert)
admin.site.register(Licence)
admin.site.register(Version)
admin.site.register(Category)