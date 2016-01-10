#!/usr/bin/python
# -*- coding: utf-8 -*-

# Import from django
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView

# Import from zds
from zds import settings
from zds.poll.forms import (PollForm, PollInlineFormSet,
    ChoiceFormSetHelper, UpdatePollForm)
from zds.poll.models import (Poll, MultipleVote, RangeVote,
    UNIQUE_VOTE_KEY, RANGE_VOTE_KEY, MULTIPLE_VOTE_KEY)
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
        # Initialize the form if the user is authenticated
        # and has voted
        initial_data = None
        if self.request.user.is_authenticated():
            # Get the user votes if is authenticated
            user_vote = poll.get_user_vote(self.request.user)
            if user_vote:
                # Unique vote
                if poll.type_vote == UNIQUE_VOTE_KEY:
                    initial_data = {'choice': user_vote[0]['choice_id']}
                # Multiple vote
                elif poll.type_vote == MULTIPLE_VOTE_KEY:
                    choices = [vote['choice_id'] for vote in user_vote]
                    initial_data = {'choices': choices}
                # Range vote
                elif poll.type_vote == RANGE_VOTE_KEY:
                    print user_vote
                    initial_data = user_vote

        context['form'] = poll.get_vote_form(initial=initial_data)
        return context

    @method_decorator(login_required)
    def post(self, request, pk):
        poll = get_object_or_404(Poll, pk=pk)

        if not poll.open:
            return HttpResponseForbidden()

        form = poll.get_vote_form(data=request.POST)

        # Vote unique
        if poll.type_vote == UNIQUE_VOTE_KEY:
            if form.is_valid():
                try:
                    vote = form.save(commit=False)
                    vote.poll = poll
                    vote.user = request.user
                    vote.save()
                except IntegrityError:
                    return HttpResponseForbidden()
        # Vote multiple
        elif poll.type_vote == MULTIPLE_VOTE_KEY:
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
            if form.is_valid():
                for range_vote in form.cleaned_data:
                    vote = RangeVote(
                        poll=poll,
                        user=request.user,
                        choice=range_vote['choice'],
                        range=range_vote['range']
                    )
                    vote.save()
        return redirect('poll-details', pk=poll.pk)


class UpdatePoll(LoginRequiredMixin, UpdateView):
    model = Poll
    template_name = 'poll/update.html'
    context_object_name = 'poll'
    form_class = UpdatePollForm


class DeletePoll(LoginRequiredMixin, DeleteView):
    model = Poll
    template_name = 'poll/delete.html'
    context_object_name = 'poll'

    def get_success_url(self):
        return reverse('poll-list')
