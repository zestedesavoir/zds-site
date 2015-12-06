#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404

from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView
from django.forms import modelformset_factory

from zds import settings
from zds.poll.forms import PollForm, PollInlineFormSet, ChoiceFormSetHelper,\
    UniqueVoteForm, MultipleVoteForm, RangeVoteModelForm, RangeVoteFormSet, \
    UpdatePollForm
from zds.poll.models import Poll, MultipleVote, RangeVote,\
    UNIQUE_VOTE_KEY, RANGE_VOTE_KEY, MULTIPLE_VOTE_KEY
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

        # Choices
        formset = PollInlineFormSet(self.request.POST, instance=poll)
        if formset.is_valid():
            poll.save()
            formset.save()
        else:
            return self.render_to_response(self.get_context_data(form=form))

        return redirect('poll-details', pk=poll.pk)


class DetailsPoll(DetailView):
    model = Poll
    template_name = 'poll/detail.html'
    context_object_name = 'poll'

    def get_context_data(self, **kwargs):
        context = super(DetailsPoll, self).get_context_data(**kwargs)
        poll = context['poll']
        context['form'] = poll.get_form_class()
        return context

    @method_decorator(login_required)
    def post(self, request, pk):
        poll = get_object_or_404(Poll, pk=pk)

        if not poll.open:
            return HttpResponseForbidden()

        # Vote unique
        if poll.type_vote == UNIQUE_VOTE_KEY:
            form = UniqueVoteForm(poll=poll, data=request.POST)
            print request.POST
            print form.data
            if form.is_valid():
                print "unique is valid !!"
                vote = form.save(commit=False)
                vote.poll = poll
                vote.user = request.user
                vote.save()
            else:
                print "unique invalid"
                print form.errors
        # Vote multiple
        elif poll.type_vote == MULTIPLE_VOTE_KEY:
            form = MultipleVoteForm(poll=poll, data=request.POST)
            if form.is_valid():
                for choice in form.cleaned_data['choices']:
                    vote = MultipleVote(
                        poll=poll,
                        user=request.user,
                        choice=choice
                    )
                    vote.save()
        # Range vote
        elif poll.type_vote == RANGE_VOTE_KEY:
            range_vote_formset = modelformset_factory(
                RangeVote,
                form=RangeVoteModelForm,
                formset=RangeVoteFormSet
            )
            form = range_vote_formset(poll=poll, data=request.POST)
            if form.is_valid():
                for range_vote in form.cleaned_data:
                    vote = RangeVote(
                        poll=poll,
                        user=request.user,
                        choice=range_vote['choice'],
                        range=range_vote['range']
                    )
                    vote.save()
            else:
                # return self.render_to_response(self.get_context())
                print "invalid !!"
                print form.errors
        return redirect('poll-details', pk=poll.pk)


class UpdatePoll(UpdateView):
    model = Poll
    template_name = 'poll/update.html'
    context_object_name = 'poll'
    form_class = UpdatePollForm


class DeletePoll(DeleteView):
    model = Poll
    template_name = 'poll/delete.html'
    context_object_name = 'poll'

    def get_success_url(self):
        return reverse('poll-list')
