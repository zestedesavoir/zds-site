# coding: utf-8

from django.template import RequestContext, defaultfilters

from django.shortcuts import render_to_response
from git import Repo
from django.conf import settings


try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()


def get_current_user():
    return getattr(_thread_locals, 'user', None)


def get_current_request():
    return getattr(_thread_locals, 'request', None)


def get_git_version():
    try:
        repo = Repo(settings.SITE_ROOT)
        branch = repo.active_branch
        commit = repo.head.commit.hexsha
        v = u"{0}/{1}".format(branch, commit[:7])
        return {'name': v, 'url': u'{}/tree/{}'.format(settings.ZDS_APP['site']['repository'], commit)}
    except:
        return {'name': '', 'url': ''}


class ThreadLocals(object):

    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        _thread_locals.request = request


def render_template(tmpl, dct=None):
    if dct is None:
        dct = {}
    dct['git_version'] = get_git_version()
    dct['app'] = settings.ZDS_APP
    return render_to_response(
        tmpl, dct, context_instance=RequestContext(get_current_request()))


def slugify(text):
    if defaultfilters.slugify(text).strip('') == '':
        return '--'
    else:
        return defaultfilters.slugify(text)
