from django.contrib import admin

from zds.pages.models import GroupContact


class GroupContactAdmin(admin.ModelAdmin):

    """Representation of GroupContact model in the admin interface."""

    raw_id_fields = ('person_in_charge',)


admin.site.register(GroupContact, GroupContactAdmin)
