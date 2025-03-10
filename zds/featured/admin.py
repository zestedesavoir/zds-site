from django.contrib import admin

from zds.featured.models import FeaturedMessage, FeaturedResource

admin.site.register(FeaturedResource)
admin.site.register(FeaturedMessage)
