#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView

from zds import settings
from zds.member.decorator import LoginRequiredMixin
from zds.poll.forms import PollForm, PollInlineFormSet, ChoiceFormSetHelper, UpdatePollForm
from zds.poll.models import Poll
from zds.utils import slugify
from zds.utils.paginator import ZdSPagingListView


class ListPoll(LoginRequiredMixin, ZdSPagingListView):
    """Display the poll list of a user"""

    model = Poll
    template_name = 'poll/list.html'
    context_object_name = 'polls'
    paginate_by = settings.ZDS_APP['poll']['poll_per_page']

    def get_queryset(self):
        return Poll.objects.filter(author=self.request.user)


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
        poll.author = self.request.user
        poll.slug = slugify(form.cleaned_data['title'])

        # Choices
        formset = PollInlineFormSet(self.request.POST, instance=poll)
        if formset.is_valid():
            poll.save()
            formset.save()
            return redirect('poll-details', pk=poll.pk)

        return self.render_to_response(self.get_context_data(form=form))


class DetailsPoll(DetailView):
    model = Poll
    template_name = 'poll/detail.html'
    context_object_name = 'poll'


class UpdatePoll(LoginRequiredMixin, UpdateView):
    model = Poll
    template_name = 'poll/update.html'
    context_object_name = 'poll'
    form_class = UpdatePollForm

    def get_object(self, queryset=None):
        poll = super(UpdatePoll, self).get_object()
        if poll.author != self.request.user:
            raise PermissionDenied
        return poll


class DeletePoll(LoginRequiredMixin, DeleteView):
    model = Poll
    template_name = 'poll/delete.html'
    context_object_name = 'poll'

    def get_success_url(self):
        return reverse('poll-list')

    def get_object(self, queryset=None):
        poll = super(DeletePoll, self).get_object()
        if poll.author != self.request.user:
            raise PermissionDenied
        return poll
