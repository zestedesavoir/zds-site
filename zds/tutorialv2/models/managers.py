from django.db.models import Manager
from django.db.models.aggregates import Count


class VerbCastManager(Manager):

    def get_verb_for_category(self, category):
        from zds.tutorialv2.models.models_database import Verb
        all_verbs = list(Verb.objects.all())
        queryset = self.filter(content__subcategory__title=category)\
            .annotate(nb_of_vote=Count("verb__label"))
        return list(set(_ for _ in all_verbs) - set(_.verb for _ in queryset))

    def get_tags_label_for_category_and_tags(self, category, tags):
        return self.filter(content__subcategory__title=category, tags__title__in=tags)\
            .distinct("verb__label")\
            .values_list("verb__label", flat=True)
