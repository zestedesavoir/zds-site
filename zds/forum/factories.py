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


def create_category_and_forum(group=None):
    category = CategoryFactory(position=1)
    forum = ForumFactory(category=category, position_in_category=1)
    if group is not None:
        forum.groups.add(group)
        forum.save()
    return category, forum


def create_topic_in_forum(forum, profile, is_sticky=False, is_solved=False, is_locked=False):
    topic = TopicFactory(forum=forum, author=profile.user)
    topic.is_sticky = is_sticky
    if is_solved:
        topic.solved_by = profile.user
    topic.is_locked = is_locked
    topic.save()
    PostFactory(topic=topic, author=profile.user, position=1)
    return topic
