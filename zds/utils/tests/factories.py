import factory

from zds.utils.models import Category, CategorySubCategory, Licence, SubCategory


class CategoryFactory(factory.django.DjangoModelFactory):
    """
    Factory that creates a Category.
    """

    class Meta:
        model = Category

    title = factory.Sequence("Ma catégorie No{}".format)
    slug = factory.Sequence("category{}".format)


class SubCategoryFactory(factory.django.DjangoModelFactory):
    """
    Factory that creates a SubCategory.
    """

    class Meta:
        model = SubCategory

    title = factory.Sequence(lambda n: f"Sous-Categorie {n} pour Tuto")
    subtitle = factory.Sequence(lambda n: f"Sous titre de Sous-Categorie {n} pour Tuto")
    slug = factory.Sequence(lambda n: f"sous-categorie-{n}")

    @classmethod
    def _generate(cls, create, attrs):
        # This parameter is only used inside _generate() and won't be saved in the database,
        # which is why we use attrs.pop() (it is removed from attrs).
        category = attrs.pop("category", None)

        subcategory = super()._generate(create, attrs)

        if category is None:
            category = CategoryFactory()

        relation = CategorySubCategory(category=category, subcategory=subcategory)
        relation.save()

        return subcategory


class LicenceFactory(factory.django.DjangoModelFactory):
    """
    Factory that creates a License.
    """

    class Meta:
        model = Licence

    code = factory.Sequence(lambda n: f"bidon-no{n + 1}")
    title = factory.Sequence(lambda n: f"Licence bidon no{n + 1}")
