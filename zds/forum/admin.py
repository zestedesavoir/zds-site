from django.contrib import admin

from zds.forum.models import Forum, ForumCategory, Post, Topic, TopicRead


class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "forum", "pubdate")
    list_filter = ("is_locked", "is_sticky")
    raw_id_fields = ("forum", "author", "last_message", "tags", "solved_by")
    ordering = ("-pubdate",)
    search_fields = ("author__username", "title", "subtitle", "github_issue")


class TopicReadAdmin(admin.ModelAdmin):
    list_display = ("topic", "user")
    raw_id_fields = ("topic", "post", "user")
    search_fields = ("topic__title", "user__username")


class PostAdmin(admin.ModelAdmin):
    list_display = ("topic", "author", "ip_address", "pubdate", "is_visible")
    list_filter = ("is_visible",)
    raw_id_fields = ("author", "editor")
    ordering = ("-pubdate",)
    search_fields = ("author__username", "text", "text_hidden", "ip_address")


admin.site.register(ForumCategory)
admin.site.register(Forum)
admin.site.register(Post, PostAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(TopicRead, TopicReadAdmin)
