# coding: utf-8

import os.path
import random
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template import Context
from django.template.loader import get_template
from zds import settings

from zds.article.models import get_last_articles
from zds.forum.models import get_last_topics
from zds.member.decorator import can_read_now, can_write_and_read_now
from zds.pages.forms import AssocSubscribeForm
from zds.settings import SITE_ROOT
from zds.tutorial.models import get_last_tutorials
from zds.utils import render_template, slugify
from zds.utils.models import Alert


@can_read_now
def home(request):
    """Display the home page with last topics added."""

    tutos = []
    for tuto in get_last_tutorials():
        data = tuto.load_json_for_public()
        data['pk'] = tuto.pk
        data['image'] = tuto.image
        data['gallery'] = tuto.gallery
        data['pubdate'] = tuto.pubdate
        data['update'] = tuto.update
        data['subcategory'] = tuto.subcategory
        data['get_absolute_url_online'] = reverse(
            'zds.tutorial.views.view_tutorial_online',
            args=[
                tuto.pk,
                slugify(
                    data['title'])])

        tutos.append(data)

    try:
        with open(os.path.join(SITE_ROOT, 'quotes.txt'), 'r') as fh:
            quote = random.choice(fh.readlines())
    except:
        quote = u'Zeste de Savoir, la connaissance pour tous et sans pépins !'

    return render_template('home.html', {
        'last_topics': get_last_topics(request.user),
        'last_tutorials': tutos,
        'last_articles': get_last_articles(),
        'quote': quote,
    })


@can_read_now
def index(request):
    return render_template('pages/index.html')


@can_read_now
def about(request):
    """Display many informations about the website."""
    return render_template('pages/about.html')


@can_write_and_read_now
@login_required
def assoc_subscribe(request):
    if request.method == "POST":
        form = AssocSubscribeForm(request.POST)
        if form.is_valid():
            user = request.user
            data = form.data
            context = {
                'first_name': data['first_name'],
                'surname': data['surname'],
                'email': data['email'],
                'justification': data['justification'],
                'username': user.username,
                'profile_url': settings.SITE_URL + reverse('zds.member.views.details',
                                                            kwargs={'user_name': user.username})
            }

            # Send email
            subject = "Demande d'adhésion de {}".format(user.username)
            from_email = "ZesteDeSavoir <noreply@zestedesavoir.com>"
            reply_to_email = "{} <{}>".format(user.username, data['email'])
            message_html = get_template("email/assoc_subscribe.html").render(Context(context))
            message_txt = get_template("email/assoc_subscribe.txt") .render(Context(context))
            msg = EmailMultiAlternatives(
                subject,
                message_txt,
                from_email,
                [settings.MAIL_CA_ASSO],
                headers={'Reply-To': reply_to_email})
            msg.attach_alternative(message_html, "text/html")
            try:
                msg.send()
                messages.success(request, "Votre demande d'adhésion a bien été envoyée et va être étudiée.")
            except:
                msg = None
                messages.error(request, "Une erreur est survenue.")
        return render_template("pages/assoc_subscribe.html", {"form": form})

    form = AssocSubscribeForm(initial={'email': request.user.email})
    return render_template("pages/assoc_subscribe.html", {"form": form})


@can_read_now
def association(request):
    """Display association's presentation."""
    return render_template('pages/association.html')


@can_read_now
def contact(request):
    """Display contact page."""
    staffs = User.objects.filter(
        groups__in=Group.objects.filter(
            name__contains='staff')).all()
    devs = User.objects.filter(
        groups__in=Group.objects.filter(
            name__contains='dev')).all()
    return render_template('pages/contact.html', {
        'staffs': staffs,
        'devs': devs
    })


@can_read_now
def eula(request):
    """End-User Licence Agreement."""
    return render_template('pages/eula.html')


@can_write_and_read_now
@login_required
def alerts(request):
    # only staff can see alerts list
    if not request.user.has_perm('forum.change_post'):
        raise PermissionDenied

    alerts = Alert.objects.all().order_by('-pubdate')

    return render_template('pages/alerts.html', {
        'alerts': alerts,
    })
