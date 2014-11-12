# coding: utf-8

from datetime import datetime, timedelta
import time

from django import template
from django.db.models import Q, F

from zds.article.models import Reaction, ArticleRead
from zds.forum.models import TopicFollowed, never_read as never_read_topic, Post, TopicRead
from zds.mp.models import PrivateTopic, PrivateTopicRead
from zds.tutorial.models import Note, TutorialRead
from zds.utils.models import Alert


register = template.Library()


@register.filter('is_read')
def is_read(topic):
    if never_read_topic(topic):
        return False
    else:
        return True


@register.filter('humane_delta')
def humane_delta(value):
    # mapping between label day and key
    const = {1: "Aujourd'hui", 2: "Hier", 3: "Cette semaine", 4: "Ce mois-ci", 5: "Cette année"}

    return const[value]


@register.filter('followed_topics')
def followed_topics(user):
    topicsfollowed = TopicFollowed.objects.select_related("topic").filter(user=user)\
        .order_by('-topic__last_message__pubdate')[:10]
    # This period is a map for link a moment (Today, yesterday, this week, this month, etc.) with
    # the number of days for which we can say we're still in the period
    # for exemple, the tuple (2, 1) means for the period "2" corresponding to "Yesterday" according
    # to humane_delta, means if your pubdate hasn't exceeded one day, we are always at "Yesterday"
    # Number is use for index for sort map easily
    period = ((1, 0), (2, 1), (3, 7), (4, 30), (5, 360))
    topics = {}
    for tf in topicsfollowed:
        for p in period:
            if tf.topic.last_message.pubdate.date() >= (datetime.now() - timedelta(days=int(p[1]),
                                                                                   hours=0, minutes=0,
                                                                                   seconds=0)).date():
                if p[0] in topics:
                    topics[p[0]].append(tf.topic)
                else:
                    topics[p[0]] = [tf.topic]
                break
    return topics


def comp(d1, d2):
    v1 = int(time.mktime(d1['pubdate'].timetuple()))
    v2 = int(time.mktime(d2['pubdate'].timetuple()))
    if v1 > v2:
        return -1
    elif v1 < v2:
        return 1
    else:
        return 0


@register.filter('interventions_topics')
def interventions_topics(user):
    topicsfollowed = TopicFollowed.objects.filter(user=user).values("topic").distinct().all()

    topics_never_read = TopicRead.objects\
        .filter(user=user)\
        .filter(topic__in=topicsfollowed)\
        .select_related("topic")\
        .exclude(post=F('topic__last_message'))

    articlesfollowed = Reaction.objects\
        .filter(author=user, article__sha_public__is_null=False)\
        .values('article')\
        .distinct().all()

    articles_never_read = ArticleRead.objects\
        .filter(user=user)\
        .filter(article__in=articlesfollowed)\
        .select_related("article")\
        .exclude(reaction=F('article__last_reaction'))

    tutorialsfollowed = Note.objects\
        .filter(author=user, tutorial__sha_public__is_null=False)\
        .values('tutorial')\
        .distinct().all()

    tutorials_never_read = TutorialRead.objects\
        .filter(user=user)\
        .filter(tutorial__in=tutorialsfollowed)\
        .exclude(note=F('tutorial__last_note'))

    posts_unread = []

    for art in articles_never_read:
        content = art.article.first_unread_reaction()
        posts_unread.append({'pubdate': content.pubdate,
                             'author': content.author,
                             'title': art.article.title,
                             'url': content.get_absolute_url()})

    for tuto in tutorials_never_read:
        content = tuto.tutorial.first_unread_note()
        posts_unread.append({'pubdate': content.pubdate,
                             'author': content.author,
                             'title': tuto.tutorial.title,
                             'url': content.get_absolute_url()})

    for top in topics_never_read:
        content = top.topic.first_unread_post()
        if content is None:
            content = top.topic.last_message
        posts_unread.append({'pubdate': content.pubdate,
                             'author': content.author,
                             'title': top.topic.title,
                             'url': content.get_absolute_url()})

    posts_unread.sort(cmp=comp)

    return posts_unread


@register.filter('interventions_privatetopics')
def interventions_privatetopics(user):

    topics_never_read = list(PrivateTopicRead.objects
                             .filter(user=user)
                             .filter(privatepost=F('privatetopic__last_message')).all())

    tnrs = []
    for tnr in topics_never_read:
        tnrs.append(tnr.privatetopic.pk)

    privatetopics_unread = PrivateTopic.objects\
        .filter(Q(author=user) | Q(participants__in=[user]))\
        .exclude(pk__in=tnrs)\
        .select_related("privatetopic")\
        .order_by("-pubdate")\
        .distinct()

    return {'unread': privatetopics_unread}


@register.filter(name='alerts_list')
def alerts_list(user):
    total = []
    alerts = Alert.objects.select_related("author").all().order_by('-pubdate')[:10]
    for alert in alerts:
        if alert.scope == Alert.FORUM:
            post = Post.objects.select_related("topic").get(pk=alert.comment.pk)
            total.append({'title': post.topic.title,
                          'url': post.get_absolute_url(),
                          'pubdate': post.pubdate,
                          'author': alert.author,
                          'text': alert.text})
        if alert.scope == Alert.ARTICLE:
            reaction = Reaction.objects.select_related("article").get(pk=alert.comment.pk)
            total.append({'title': reaction.article.title,
                          'url': reaction.get_absolute_url(),
                          'pubdate': reaction.pubdate,
                          'author': alert.author,
                          'text': alert.text})
        if alert.scope == Alert.TUTORIAL:
            note = Note.objects.select_related("tutorial").get(pk=alert.comment.pk)
            total.append({'title': note.tutorial.title,
                          'url': note.get_absolute_url(),
                          'pubdate': note.pubdate,
                          'author': alert.author,
                          'text': alert.text})

    return total


@register.filter(name='alerts_count')
def alerts_count(user):
    if user.is_authenticated():
        return Alert.objects.count()
    else:
        return 0
