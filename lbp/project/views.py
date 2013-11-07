# coding: utf-8

from datetime import datetime
from django.conf import settings

from django.shortcuts import get_object_or_404, redirect
from django.http import Http404

from django.contrib.auth.decorators import login_required

from lbp.utils import render_template, slugify
from lbp.utils.models import DateManager
from lbp.gallery.models import Gallery, Image, UserGallery

from .models import Project, Participation, Category, Plateform, Technology, BPlan, Fonction
from .forms import ProjectForm, ProjectDetailsForm, ProjectStrategyForm, ProjectMarketStudyForm, ProjectRoadmapForm


def index(request):
    '''Affiche la liste des projects'''
    projects = Project.objects.all()\
        .order_by('date__update')

    if request.user.is_authenticated():
        user_participation = Participation.objects.filter(user=request.user)
    else:
        user_participation = None

    return render_template('project/index.html', {
        'projects': projects,
        'participations': user_participation
    })
    
@login_required
def new(request):
    '''Créer un nouveau project'''
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        
        if 'image' in request.FILES: 
            if request.FILES['image'].size > settings.IMAGE_MAX_SIZE:
                raise Http404
            
        if form.is_valid():
            data = form.data

            project = Project()
            project.title = data['title']
            project.description = data['description']
            project.slug = slugify(data['title'])
            project.author = request.user
            
            
            dt = DateManager()
            dt.create_at = datetime.now()
            dt.update = datetime.now()
            dt.save()
            project.date = dt
            # on enregistre d'abord les champs de base
            project.save()
            
            # Creating the gallery
            gal = Gallery()
            gal.title = data['title']
            gal.slug = slugify(data['title'])
            gal.pubdate = datetime.now()
            gal.save()

            # Attach user to gallery
            userg = UserGallery()
            userg.gallery = gal
            userg.mode = 'W'  # write mode
            userg.user = request.user
            userg.save()
            
            project.gallery = gal
            project.save()
            
            # Create image
            if 'image' in request.FILES:
                img = Image()
                img.physical = request.FILES['image']
                img.gallery = gal
                img.title = request.FILES['image']
                img.slug = slugify(request.FILES['image'])
                img.pubdate = datetime.now()
                img.save()
                
                project.image = img
                project.save()
            
            if 'categories' in request.POST:
                for cat in data['categories']:
                    project.categories.add(cat)
                project.save()
            
            if 'plateforms' in request.POST:
                for plt in data['plateforms']:
                    project.plateforms.add(plt)
                project.save()
            
            if 'technologies' in request.POST:
                for techno in data['technologies']:
                    project.categories.add(techno)
                project.save()
                
            return redirect(project.get_absolute_url())
    else:
        form = ProjectForm()

    return render_template('project/new.html', {
        'form': form
    })

def view_general(request, prj_pk, prj_slug):
    '''View a project'''
    project = get_object_or_404(Project, pk=prj_pk)
    
    if prj_slug != slugify(project.title):
        return redirect(project.get_absolute_url())
    
    return render_template('project/view_general.html', {
        'project': project
    })

@login_required
def edit_general(request, prj_pk, prj_slug):
    '''Edit a project'''
    project = get_object_or_404(Project, pk=prj_pk)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        
        if 'image' in request.FILES: 
            if request.FILES['image'].size > settings.IMAGE_MAX_SIZE:
                raise Http404
            
        if form.is_valid():
            data = form.data

            project.titre = data['title']
            project.description = data['description']
            project.text = data['text']
            project.date.update = datetime.now()
            
            project.categories.clear()
            if 'categories' in data :
                for c in data['categories']: 
                    project.categories.add(c)
                project.save()
            
            project.technologies.clear()
            if 'technologies' in data :
                for t in data['technologies']:
                    project.technologies.add(t)
                project.save() 
                
            project.platforms.clear()
            if 'platforms' in data :
                for p in data['platforms']:
                    project.platforms.add(p)
                project.save() 
            
            # Update image
            if 'image' in request.FILES:
                img = Image()
                img.physical = request.FILES['image']
                img.gallery = news.gallery
                img.title = request.FILES['image']
                img.slug = slugify(request.FILES['image'])
                img.update = datetime.now()
                img.save()
                
                project.image=img
                project.save()

            project.save()
            return redirect(project.get_absolute_url())
    else:

        form = ProjectForm({
            'title': project.title,
            'description': project.description,
            'categories': project.categories.all(),
            'technologies': project.technologies.all(),
            'plateforms': project.plateforms.all(),
        })
    
    return render_template('project/edit.html', {
        'project': project,
        'form': form
    })

def view_details(request, prj_pk, prj_slug):
    '''View a project'''
    project = get_object_or_404(Project, pk=prj_pk)
    
    if prj_slug != slugify(project.title):
        return redirect(project.get_absolute_url())
    
    return render_template('project/view_details.html', {
        'project': project
    })

@login_required
def edit_details(request, prj_pk, prj_slug):
    '''Edit a project'''
    project = get_object_or_404(Project, pk=prj_pk)
    if not project.bplan :
        bplan = BPlan()
        bplan.save()
        project.bplan=bplan
        project.save()
    
    if request.method == 'POST':
        form = ProjectDetailsForm(request.POST)
            
        if form.is_valid():
            data = form.data
            project.bplan.short_description = data['short_description']
            project.bplan.long_description = data['long_description']
            project.bplan.save()
            
            project.date.update = datetime.now()
            project.save()
            return redirect(project.get_absolute_url())
    else:

        form = ProjectDetailsForm({
            'short_description': project.bplan.short_description,
            'long_description': project.bplan.long_description,
        })
    
    return render_template('project/edit.html', {
        'project': project,
        'form': form
    })

def view_strategy(request, prj_pk, prj_slug):
    '''View a project'''
    project = get_object_or_404(Project, pk=prj_pk)
    
    if prj_slug != slugify(project.title):
        return redirect(project.get_absolute_url())
    
    return render_template('project/view_strategy.html', {
        'project': project
    })


@login_required
def edit_strategy(request, prj_pk, prj_slug):
    '''Edit a project'''
    project = get_object_or_404(Project, pk=prj_pk)
    if not project.bplan :
        bplan = BPlan()
        bplan.save()
        project.bplan=bplan
        project.save()
    
    if request.method == 'POST':
        form = ProjectStrategyForm(request.POST)
            
        if form.is_valid():
            data = form.data

            project.bplan.product = data['product']
            project.bplan.pricing = data['pricing']
            project.bplan.strategy = data['strategy']
            project.bplan.promote = data['promote']
            project.bplan.place = data['place']
            project.bplan.save()
            
            project.date.update = datetime.now()
            project.save()
            return redirect(project.get_absolute_url())
    else:

        form = ProjectStrategyForm({
            'product': project.bplan.product,
            'pricing': project.bplan.pricing,
            'strategy': project.bplan.strategy,
            'promote': project.bplan.promote,
            'place': project.bplan.place,
        })
    
    return render_template('project/edit.html', {
        'project': project,
        'form': form
    })


def view_roadmap(request, prj_pk, prj_slug):
    '''View a project'''
    project = get_object_or_404(Project, pk=prj_pk)
    
    if prj_slug != slugify(project.title):
        return redirect(project.get_absolute_url())
    
    return render_template('project/view_roadmap.html', {
        'project': project
    })

@login_required
def edit_roadmap(request, prj_pk, prj_slug):
    '''Edit a project'''
    project = get_object_or_404(Project, pk=prj_pk)
    if not project.bplan :
        bplan = BPlan()
        bplan.save()
        project.bplan=bplan
        project.save()
    
    if request.method == 'POST':
        form = ProjectRoadmapForm(request.POST)

        if form.is_valid():
            data = form.data

            project.bplan.roadmap = data['roadmap']
            project.bplan.save()
            
            project.date.update = datetime.now()
            project.save()
            return redirect(project.get_absolute_url())
    else:

        form = ProjectRoadmapForm({
            'roadmap': project.bplan.roadmap,
        })
    
    return render_template('project/edit.html', {
        'project': project,
        'form': form
    })

def view_history(request, prj_pk, prj_slug):
    '''View a project'''
    project = get_object_or_404(Project, pk=prj_pk)
    
    if prj_slug != slugify(project.title):
        return redirect(project.get_absolute_url())
    
    return render_template('project/view_history.html', {
        'project': project
    })

def view_marketstudy(request, prj_pk, prj_slug):
    '''View a project'''
    project = get_object_or_404(Project, pk=prj_pk)
    
    if prj_slug != slugify(project.title):
        return redirect(project.get_absolute_url())
    
    return render_template('project/view_marketstudy.html', {
        'project': project
    })

@login_required
def edit_marketstudy(request, prj_pk, prj_slug):
    '''Edit a project'''
    project = get_object_or_404(Project, pk=prj_pk)
    if not project.bplan :
        bplan = BPlan()
        bplan.save()
        project.bplan=bplan
        project.save()
    
    if request.method == 'POST':
        form = ProjectMarketStudyForm(request.POST)

        if form.is_valid():
            data = form.data

            project.bplan.market_study = data['market_study']
            project.bplan.save()
            
            project.date.update = datetime.now()
            project.save()
            return redirect(project.get_absolute_url())
    else:

        form = ProjectMarketStudyForm({
            'market_study': project.bplan.market_study,
        })
    
    return render_template('project/edit.html', {
        'project': project,
        'form': form
    })

def recrutement(request, prj_pk, prj_slug):
    '''Recrute for project'''
    project = get_object_or_404(Project, pk=prj_pk)
    
    if request.user.is_authenticated():
        user_participation = Participation.objects.filter(user=request.user)
    else:
        user_participation = None
    
    return render_template('project/recrutement.html', {
        'project': project,
        'participations': user_participation
    })
    
    