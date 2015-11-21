#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import redirect
from django.views.generic import CreateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from zds import settings

from zds.poll.forms import PollForm, ChoiceForm, PollInlineFormSet, ChoiceFormSetHelper
from zds.poll.models import Poll, Choice
from zds.utils import slugify
from zds.utils.paginator import ZdSPagingListView


class ListPoll(ZdSPagingListView):
    model = Poll
    template_name = 'poll/list.html'
    context_object_name = 'polls'
    paginate_by = settings.ZDS_APP['poll']['poll_per_page']


class NewPoll(CreateView):
    model = Poll
    template_name = 'poll/new.html'
    form_class = PollForm

    def get_context_data(self, **kwargs):
        context = super(NewPoll, self).get_context_data(**kwargs)
        context['helper'] = ChoiceFormSetHelper()
        if self.request.POST:
            context['formset'] = PollInlineFormSet(self.request.POST)
        else:
            context['formset'] = PollInlineFormSet()
        return context

    def form_valid(self, form):
        poll = form.save(commit=False)
        poll.user = self.request.user
        poll.slug = slugify(form.cleaned_data['title'])

        formset = PollInlineFormSet(self.request.POST, instance=poll)
        if formset.is_valid():
            poll.save()
            formset.save()
        else:
            return self.render_to_response(self.get_context_data(form=form))

        return redirect('poll-list')


class DetailsPoll(DetailView):
    model = Poll
    template_name = 'poll/detail.html'
    context_object_name = 'poll'


class DeletePoll(DeleteView):
    model = Poll
    template_name = 'poll/delete.html'
    context_object_name = 'poll'