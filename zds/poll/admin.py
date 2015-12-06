from django.contrib import admin

from zds.poll.models import Poll, Choice, RangeVote, UniqueVote

admin.site.register(Poll)
admin.site.register(Choice)
admin.site.register(RangeVote)
admin.site.register(UniqueVote)