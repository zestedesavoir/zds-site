# coding: utf-8

from django import template

from zds.article.models import never_read as never_read_article, Validation as ArticleValidation, Reaction
from zds.forum.models import TopicFollowed, never_read as never_read_topic, Post
from zds.mp.models import PrivateTopic, never_privateread
from zds.utils.models import Alert
from zds.tutorial.models import never_read as never_read_tutorial, Validation as TutoValidation, Note


register = template.Library()


@register.filter('is_read')
def is_read(topic):
    if never_read_topic(topic):
        return False
    else:
        return True


@register.filter('followed_topics')
def followed_topics(user):
    topicsfollowed = TopicFollowed.objects.filter(user=user)\
        .order_by('-topic__last_message__pubdate')[:10]
    topics = []
    for tf in topicsfollowed:
        topics.append(tf.topic)
    return topics


@register.filter('interventions_topics')
def interventions_topics(user):
    topicsfollowed = TopicFollowed.objects.filter(user=user)\
        .order_by('-topic__last_message__pubdate')

    posts_unread = []

    for topicfollowed in topicsfollowed:
        if never_read_topic(topicfollowed.topic):
            posts_unread.append((topicfollowed.topic.first_unread_post()))

    return posts_unread


@register.filter('interventions_privatetopics')
def interventions_privatetopics(user):
    topicsfollowed = PrivateTopic.objects.filter(author=user)\
        .order_by('-last_message__pubdate')
    topicspart = PrivateTopic.objects.filter(participants__in=[user])\
        .order_by('-last_message__pubdate')
    privatetopics_unread = []
    privatetopics_read = []

    for topicfollowed in topicsfollowed:
        if never_privateread(topicfollowed):
            privatetopics_unread.append(topicfollowed)
        else:
            privatetopics_read.append(topicfollowed)

    for topicpart in topicspart:
        if never_privateread(topicpart):
            privatetopics_unread.append(topicpart)
        else:
            privatetopics_read.append(topicpart)

    privateread_topics_count = 5 - \
        (len(privatetopics_unread) if len(privatetopics_unread) < 5 else 5)
    return {'unread': privatetopics_unread,
            'read': privatetopics_read[:privateread_topics_count]}


@register.simple_tag(name='reads_topic')
def reads_topic(topic, user):
    if user.is_authenticated():
        if never_read_topic(topic, user):
            return ''
        else:
            return 'secondary'
    else:
        return ''


@register.simple_tag(name='reads_article')
def reads_article(article, user):
    if user.is_authenticated():
        if never_read_article(article, user):
            return ''
        else:
            return 'secondary'
    else:
        return ''


@register.simple_tag(name='reads_tutorial')
def reads_tutorial(tutorial, user):
    if user.is_authenticated():
        if never_read_tutorial(tutorial, user):
            return ''
        else:
            return 'secondary'
    else:
        return ''


@register.filter(name='alerts_validation_tutos')
def alerts_validation_tutos(user):
    tutos = TutoValidation.objects.order_by('-date_proposition').all()
    total = []
    for tuto in tutos:
        if tuto.is_pending():
            total.append(tuto)

    return {'total': len(total), 'alert': total[:5]}


@register.filter(name='alerts_validation_articles')
def alerts_validation_articles(user):
    articles = ArticleValidation.objects.order_by('-date_proposition').all()
    total = []
    for article in articles:
        if article.is_pending():
            total.append(article)

    return {'total': len(total), 'alert': total[:5]}


@register.filter(name='alerts_list')
def alerts_list(user):
    total = []
    alerts = Alert.objects.all().order_by('-pubdate')[:10]
    for alert in alerts:
        if alert.scope == Alert.FORUM:
            post = Post.objects.get(pk=alert.comment.pk)
            total.append({'title': post.topic.title,
                          'url': post.get_absolute_url(),
                          'pubdate': post.pubdate,
                          'author': alert.author})
        if alert.scope == Alert.ARTICLE:
            reaction = Reaction.objects.get(pk=alert.comment.pk)
            total.append({'title': reaction.article.title,
                          'url': reaction.get_absolute_url(),
                          'pubdate': reaction.pubdate,
                          'author': alert.author})
        if alert.scope == Alert.TUTORIAL:
            note = Note.objects.get(pk=alert.comment.pk)
            total.append({'title': note.tutorial.title,
                          'url': note.get_absolute_url(),
                          'pubdate': note.pubdate,
                          'author': alert.author})

    return total


@register.filter(name='alerts_count')
def alerts_count(user):
    if user.is_authenticated():
        return Alert.objects.count()
    else:
        return 0
