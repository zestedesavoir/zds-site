
from django.db.models import Q
from django.utils.html import escape
from project.models import Category
from ajax_select import LookupChannel


class CategoryLookup(LookupChannel):

    model = Category

    def get_query(self, category, request):
        return Category.objects.filter(title__icontains=category).order_by('title')

    def get_result(self, obj):
        u""" result is the simple text that is the completion of what the person typed """
        return obj.title

    def format_match(self, obj):
        """ (HTML) formatted item for display in the dropdown """
        return u"%s<div><i>%s</i></div>" % (escape(obj.title), escape(obj.description))
        # return self.format_item_display(obj)

    def format_item_display(self, obj):
        """ (HTML) formatted item for displaying item in the selected deck area """
        return u"%s<div><i>%s</i></div>" % (escape(obj.title), escape(obj.description))