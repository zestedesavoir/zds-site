from django.contrib import admin

from zds.stats.models import Country, City, OS, Log, Device, Browser

admin.site.register(Country)
admin.site.register(City)
admin.site.register(OS)
admin.site.register(Log)
admin.site.register(Device)
admin.site.register(Browser)
