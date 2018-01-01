from django.contrib import admin

from zds.featured.models import FeaturedResource, FeaturedMessage

admin.site.register(FeaturedResource)
admin.site.register(FeaturedMessage)
