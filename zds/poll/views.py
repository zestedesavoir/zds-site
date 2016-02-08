#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView
from django.http import JsonResponse

from zds import settings
from zds.poll.forms import (PollForm, PollInlineFormSet,
    ChoiceFormSetHelper, UpdatePollForm, get_vote_form)
from zds.poll.models import (Poll, MultipleVote,
    UNIQUE_VOTE_KEY, MULTIPLE_VOTE_KEY, UniqueVote)
from zds.member.decorator import LoginRequiredMixin
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
            user_vote = poll.get_user_vote_dict(self.request.user)
            if user_vote:
                # Unique vote
                if poll.type_vote == UNIQUE_VOTE_KEY:
                    initial_data = {'choice': user_vote[0]['choice_id']}
                # Multiple vote
                elif poll.type_vote == MULTIPLE_VOTE_KEY:
                    choices = [vote['choice_id'] for vote in user_vote]
                    initial_data = {'choices': choices}

        context['form'] = get_vote_form(poll, initial=initial_data)
        return context

    def get(self, request, *args, **kwargs):
        response = super(DetailsPoll, self).get(request, *args, **kwargs)
        if request.is_ajax():
            poll = self.get_object()
            poll_dict ={
                'title': poll.title
            }
            return JsonResponse(poll_dict)
        return response

    @method_decorator(login_required)
    def post(self, request, pk):
        poll = get_object_or_404(Poll, pk=pk)

        if not poll.is_open():
            raise PermissionDenied

        form = get_vote_form(poll, data=request.POST)

        # Vote unique
        if poll.type_vote == UNIQUE_VOTE_KEY:
            if form.is_valid():
                try:
                    vote = UniqueVote.objects.get(poll=poll, user=request.user)
                    vote.choice = form.cleaned_data['choice']
                    vote.save()
                except UniqueVote.DoesNotExist:
                    vote = form.save(commit=False)
                    vote.poll = poll
                    vote.user = request.user
                    vote.save()
        # Vote multiple
        elif poll.type_vote == MULTIPLE_VOTE_KEY:
            if form.is_valid():
                # If the user has already voted, get the list of the choices
                user_choices = [vote.choice for vote in poll.get_user_vote_objects(request.user)]
                for choice in poll.choices.all():
                    # Value form the database
                    user_has_voted = choice in user_choices
                    # Value form the form
                    user_has_selected = choice in form.cleaned_data['choices']

                    if user_has_voted and not user_has_selected:
                        # Delete vote
                        vote = MultipleVote.objects.get(
                            poll=poll,
                            user=request.user,
                            choice=choice
                        )
                        vote.delete()
                    elif not user_has_voted and user_has_selected:
                        # Create vote
                        vote = MultipleVote(
                            poll=poll,
                            user=request.user,
                            choice=choice
                        )
                        vote.save()
        return redirect('poll-details', pk=poll.pk)


class UpdatePoll(LoginRequiredMixin, UpdateView):
    model = Poll
    template_name = 'poll/update.html'
    context_object_name = 'poll'
    form_class = UpdatePollForm

    def get_object(self, queryset=None):
        poll = super(UpdatePoll, self).get_object()
        if not poll.author == self.request.user:
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
        if not poll.author == self.request.user:
            raise PermissionDenied
        return poll
