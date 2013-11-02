# coding: utf-8

from datetime import datetime

from django.shortcuts import get_object_or_404, redirect
from django.http import Http404

from django.contrib.auth.decorators import login_required

from lbp.utils import render_template, slugify

from .models import Project, Participation
from .forms import ProjectForm


def index(request):
    '''Affiche la liste des projects'''
    project = Project.objects.all()\
        .order_by('date__update')

    if request.user.is_authenticated():
        user_participation = Participation.objects.filter(user=request.user)
    else:
        user_participation = None

    return render_template('project/index.html', {
        'projects': project[:4],
        'participations': user_participation
    })
    
@login_required
def new(request):
    '''Créer un nouveau project'''
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.data

            project = Project()
            project.title = data['title']
            project.description = data['description']
            
            
            dt = DateManager()
            dt.create_at = datetime.now()
            dt.update = datetime.now()
            dt.save()
            project.date = dt
            # on enregistre d'abord les champs de base
            actualite.save()
            
            #on rajoute ensuite l'auteur de l'actualité
            participation= Participation()
            actualite.auteurs.add(request.user)
            actualite.save()

            list_tags = data['tags'].split(',')
            for tag in list_tags:
                actualite.tags.add(tag)
            actualite.save()
            return redirect(actualite.get_absolute_url())
    else:
        form = ProjectForm()

    return render_template('project/new.html', {
        'form': form
    })