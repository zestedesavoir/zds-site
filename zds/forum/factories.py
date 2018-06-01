import factory
from zds.forum.models import Category, Forum, Topic, Post
from zds.utils.models import Tag


class CategoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = Category

    title = factory.Sequence('Ma catégorie No{0}'.format)
    slug = factory.Sequence('category{0}'.format)


class ForumFactory(factory.DjangoModelFactory):
    class Meta:
        model = Forum

    title = factory.Sequence('Mon Forum No{0}'.format)
    subtitle = factory.Sequence('Sous Titre du Forum No{0}'.format)
    slug = factory.Sequence('forum{0}'.format)


class TagFactory(factory.DjangoModelFactory):
    class Meta:
        model = Tag

    title = factory.Sequence('Tag{0}'.format)
    slug = factory.Sequence('tag{0}'.format)


class TopicFactory(factory.DjangoModelFactory):
    class Meta:
        model = Topic

    title = factory.Sequence('Mon Sujet No{0}'.format)
    subtitle = factory.Sequence('Sous Titre du sujet No{0}'.format)


class PostFactory(factory.DjangoModelFactory):
    class Meta:
        model = Post

    ip_address = '192.168.3.1'
    text = "Bonjour, je me présente, je m'appelle l'homme au texte bidonné"
    text_html = text

    @classmethod
    def _prepare(cls, create, **kwargs):
        post = super(PostFactory, cls)._prepare(create, **kwargs)
        topic = kwargs.pop('topic', None)
        if topic:
            post.save()
            topic.last_message = post
            topic.save()
        return post
