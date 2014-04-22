# coding: utf-8

from zds.member.views import get_client_ip
from zds.utils import render_template

from .forms import NewsletterForm
from .models import Newsletter


def add_newsletter(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        my_ip = get_client_ip(request)
        already = Newsletter.objects.filter(ip=my_ip).count()

        if form.is_valid() and already == 0:
            data = form.data
            print data['email']
            nl = Newsletter()
            nl.email = data['email']
            nl.ip = my_ip
            nl.save()

            return render_template('newsletter/confirm.html')

        else:
            # TODO: add errors to the form and return it
            return render_template('newsletter/failed.html')
    else:
        form = NewsletterForm()
        return render_template('newsletter/new_newsletter.html', {
            'form': form
        })
