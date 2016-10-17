from django.db.models import Manager


class VerbCastManager(Manager):

    def get_tags_label_for_category(self, category):
        return self.filter(content__subcategory=category)\
            .distinct("verb__label")\
            .values_list("verb__label")

    def get_tags_label_for_category_and_tags(self, category, tags):
        return self.filter(content__subcategory=category, tags__title__in=tags)\
            .distinct("verb__label")\
            .values_list("verb__label")
