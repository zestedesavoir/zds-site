import factory
from zds.forum.models import ForumCategory, Forum, Topic, Post
from zds.utils.models import Tag


class ForumCategoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = ForumCategory

    title = factory.Sequence("Ma catégorie No{}".format)
    slug = factory.Sequence("category{}".format)


class ForumFactory(factory.DjangoModelFactory):
    class Meta:
        model = Forum

    title = factory.Sequence("Mon Forum No{}".format)
    subtitle = factory.Sequence("Sous Titre du Forum No{}".format)
    slug = factory.Sequence("forum{}".format)


class TagFactory(factory.DjangoModelFactory):
    class Meta:
        model = Tag

    title = factory.Sequence("Tag{}".format)
    slug = factory.Sequence("tag{}".format)


class TopicFactory(factory.DjangoModelFactory):
    class Meta:
        model = Topic

    title = factory.Sequence("Mon Sujet No{}".format)
    subtitle = factory.Sequence("Sous Titre du sujet No{}".format)


class PostFactory(factory.DjangoModelFactory):
    class Meta:
        model = Post

    ip_address = "192.168.3.1"
    text = "Bonjour, je me présente, je m'appelle l'homme au texte bidonné"
    text_html = text

    @classmethod
    def _prepare(cls, create, **kwargs):
        post = super()._prepare(create, **kwargs)
        topic = kwargs.pop("topic", None)
        if topic:
            post.save()
            topic.last_message = post
            topic.save()
        return post


def create_category_and_forum(group=None):
    category = ForumCategoryFactory(position=1)
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
