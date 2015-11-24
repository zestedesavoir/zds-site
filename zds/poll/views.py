#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import CreateView, DeleteView
from django.views.generic.detail import DetailView

from zds import settings
from zds.poll.forms import PollForm, PollInlineFormSet, ChoiceFormSetHelper, UniqueVoteForm, MultipleVoteForm
from zds.poll.models import Poll
from zds.member.decorator import LoginRequiredMixin
from zds.utils import slugify
from zds.utils.paginator import ZdSPagingListView


class ListPoll(ZdSPagingListView):
    model = Poll
    template_name = 'poll/list.html'
    context_object_name = 'polls'
    paginate_by = settings.ZDS_APP['poll']['poll_per_page']


class NewPoll(LoginRequiredMixin, CreateView):
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

    def get_context_data(self, **kwargs):
        context = super(DetailsPoll, self).get_context_data(**kwargs)
        poll = context['poll']
        if poll.unique_vote:
            context['form'] = UniqueVoteForm(poll)
        else:
            context['form'] = MultipleVoteForm(poll)
        return context

    def post(self, request, pk):
        poll = get_object_or_404(Poll, pk=pk)

        if poll.unique_vote:
            form = UniqueVoteForm(poll, request.POST)
            if form.is_valid():
                vote = form.save(commit=False)
                vote.poll = poll
                vote.user = self.request.user
                vote.save()
                return redirect('poll-list')
        else:
            form = MultipleVoteForm(poll, request.POST)
            # TODO validation formulaire et save

        return redirect('poll-list')


class DeletePoll(DeleteView):
    model = Poll
    template_name = 'poll/delete.html'
    context_object_name = 'poll'

    def get_success_url(self):
        return reverse('poll-list')
