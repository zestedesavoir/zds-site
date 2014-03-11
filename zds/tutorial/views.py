# coding: utf-8
from PIL import Image as ImagePIL
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.encoding import smart_str, smart_unicode
from django.views.decorators.http import require_POST
from django.core.files import File
from django.db.models import Q
from collections import OrderedDict
import glob
import json
from lxml import etree
from operator import itemgetter, attrgetter
import os
import os.path
import re
import shutil
from urllib import urlretrieve
import urllib
from urlparse import urlparse
import zipfile

from git import *
from zds.gallery.models import Gallery, UserGallery, Image
from zds.member.decorator import can_read_now, can_write_and_read_now
from zds.member.models import Profile
from zds.member.views import get_client_ip
from zds.utils import render_template, slugify
from zds.utils.models import Category, Licence, CommentLike, CommentDislike,\
    SubCategory
from zds.utils.paginator import paginator_range
from zds.utils.templatetags.emarkdown import emarkdown
from zds.utils.tutorials import get_blob, export_tutorial_to_md

from .forms import TutorialForm, PartForm, ChapterForm, EmbdedChapterForm,\
    ExtractForm, ImportForm, NoteForm, AlertForm
from .models import Tutorial, Part, Chapter, Extract, Validation, never_read, \
    mark_read, Note


@can_read_now
def index(request):
    '''Display all public tutorials of the website.'''
    # The tag indicate what the category tutorial the user would 
    # like to display. We can display all subcategories for tutorials.
    try:
        tag = get_object_or_404(SubCategory, title = request.GET['tag'])
    except (KeyError, Http404):
        tag = None
        
    if tag == None:
        tutorials = Tutorial.objects \
                .filter(sha_public__isnull=False) \
                .order_by("-pubdate")\
                .all()
    else:
        # The tag isn't None and exist in the system. We can use it to retrieve 
        # all tutorials in the subcategory specified.
        tutorials = Tutorial.objects \
                .filter(sha_public__isnull = False, subcategory__in = [tag]) \
                .order_by("-pubdate") \
                .all()

    return render_template('tutorial/index.html', {
        'tutorials': tutorials,
    })

# Staff actions.

@can_read_now
@permission_required('tutorial.change_tutorial', raise_exception=True)
@login_required
def list_validation(request):
    '''Display tutorials list in validation'''
    # Retrieve type of the validation. Default value is all validations.
    try:
        type = request.GET['type']
    except KeyError:
        type = None

    # Get subcategory to filter validations.
    try:
        subcategory = get_object_or_404(Category, pk=request.GET['subcategory'])
    except (KeyError, Http404) :
        subcategory = None

    # Orphan validation. There aren't validator attached to the validations.
    if type == 'orphan':
        if subcategory == None:
            validations = Validation.objects \
                            .filter(validator__isnull = True, status = 'PENDING') \
                            .order_by("date_proposition") \
                            .all()
        else :
            validations = Validation.objects \
                            .filter(validator__isnull = True, status = 'PENDING', tutorial__subcategory__in=[subcategory]) \
                            .order_by("date_proposition") \
                            .all()
    
    # Reserved validation. There are a validator attached to the validations.
    elif type == 'reserved':
        if subcategory == None:
            validations = Validation.objects \
                            .filter(validator__isnull = False, status = 'PENDING_V') \
                            .order_by("date_proposition") \
                            .all()
        else :
            validations = Validation.objects \
                            .filter(validator__isnull = False, status = 'PENDING_V', tutorial__subcategory__in=[subcategory]) \
                            .order_by("date_proposition") \
                            .all()        
    
    # Default, we display all validations.
    else:
        if subcategory == None:
            validations = Validation.objects \
                            .filter(Q(status = 'PENDING') | Q(status = 'PENDING_V')) \
                            .order_by("date_proposition") \
                            .all()
        else :
            validations = Validation.objects \
                            .filter(Q(status = 'PENDING') | Q(status = 'PENDING_V')) \
                            .filter(tutorial__subcategory__in=[subcategory]) \
                            .order_by("date_proposition") \
                            .all()
    
    return render_template('tutorial/validation.html', {
        'validations': validations,
    })

@can_read_now
@permission_required('tutorial.change_tutorial', raise_exception=True)
@login_required
def reservation(request, validation_pk):
    '''Display tutorials list in validation'''
    
    validation = get_object_or_404(Validation, pk=validation_pk)
    
    if validation.validator :
        validation.validator = None
        validation.date_reserve = None
        validation.status = 'PENDING'
        validation.save()
        
        return redirect(reverse('zds.tutorial.views.list_validation'))
    
    else:
        validation.validator = request.user
        validation.date_reserve = datetime.now()
        validation.status = 'PENDING_V'
        validation.save()
        return redirect(validation.tutorial.get_absolute_url())

@can_read_now
@login_required
@permission_required('tutorial.change_tutorial', raise_exception=True)
def diff(request, tutorial_pk, tutorial_slug):
    try:
        sha = request.GET['sha']
    except KeyError:
        raise Http404
    
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)
    
    repo = Repo(tutorial.get_path())
    hcommit = repo.commit(sha)
    tdiff = hcommit.diff('HEAD~1')
    
    
    return render_template('tutorial/diff_tutorial.html', {
        'tutorial': tutorial,
        'path_add':tdiff.iter_change_type('A'),
        'path_ren':tdiff.iter_change_type('R'),
        'path_del':tdiff.iter_change_type('D'),
        'path_maj':tdiff.iter_change_type('M')
    })

@can_read_now
@login_required
def history(request, tutorial_pk, tutorial_slug):
    '''Display a tutorial'''
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

    if request.user not in tutorial.authors.all():
        if not request.user.has_perm('forum.change_tutorial'):
            raise PermissionDenied

    # Make sure the URL is well-formed
    if not tutorial_slug == slugify(tutorial.title):
        return redirect(tutorial.get_absolute_url())


    repo = Repo(tutorial.get_path())
    tree = repo.heads.master.commit.tree
    
    logs = repo.head.reference.log()
    logs = sorted(logs, key=attrgetter('time'), reverse=True)
    
    return render_template('tutorial/history_tutorial.html', {
        'tutorial': tutorial, 'logs':logs
    })

@can_write_and_read_now
@login_required
@require_POST
@permission_required('tutorial.change_tutorial', raise_exception = True)
def reject_tutorial(request):
    '''Staff reject tutorial of an author'''
    # Retrieve current tutorial;
    try:
        tutorial_pk = request.POST['tutorial']
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(Tutorial, pk = tutorial_pk)

    # If 'reject' isn't in POST request, staff don't would like reject
    # the tutorial and we redirect him to the tutorial.
    if not 'reject' in request.POST:
        redirect(tutorial.get_absolute_url())

    validation = Validation.objects\
                    .filter(tutorial__pk = tutorial_pk, version = tutorial.sha_validation)\
                    .latest('date_proposition')
    validation.comment_validator = request.POST['comment-r']
    validation.status = 'REJECT'
    validation.date_validation = datetime.now()
    validation.save()
    
    # Remove sha_validation because we rejected this version of the tutorial.
    tutorial.sha_validation = None
    tutorial.pubdate = None
    tutorial.save()
    
    return redirect(tutorial.get_absolute_url())

@can_write_and_read_now
@login_required
@require_POST
@permission_required('tutorial.change_tutorial', raise_exception = True)
def valid_tutorial(request):
    '''Staff valid tutorial of an author'''
    # Retrieve current tutorial;
    try:
        tutorial_pk = request.POST['tutorial']
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(Tutorial, pk = tutorial_pk)

    # If 'valid-tuto' isn't in POST request, staff don't would like valid
    # the tutorial and we redirect him to the tutorial.
    if not 'valid-tuto' in request.POST:
        redirect(tutorial.get_absolute_url())

    MEP(tutorial)
    validation = Validation.objects\
                    .filter(tutorial__pk = tutorial_pk, version = tutorial.sha_validation)\
                    .latest('date_proposition')
    validation.comment_validator = request.POST['comment-v']
    validation.status = 'ACCEPT'
    validation.date_validation = datetime.now()
    validation.save()
    
    # Update sha_public with the sha of validation. We don't update sha_draft.
    # So, the user can continue to edit his tutorial in offline.
    tutorial.sha_public = validation.version
    tutorial.sha_validation = None
    tutorial.pubdate = datetime.now()
    tutorial.save()
    
    return redirect(tutorial.get_absolute_url() + '?version=' + validation.version)

# User actions on tutorial.

@can_write_and_read_now
@login_required
def activ_beta(request, tutorial_pk, version):
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

    if request.user not in tutorial.authors.all():
        if not request.user.has_perm('forum.change_tutorial'):
            raise PermissionDenied

    tutorial.sha_beta = version
    tutorial.save()
    
    return redirect(tutorial.get_absolute_url_beta())

@can_write_and_read_now
@login_required
def desactiv_beta(request, tutorial_pk, version):
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

    if request.user not in tutorial.authors.all():
        if not request.user.has_perm('forum.change_tutorial'):
            raise PermissionDenied

    tutorial.sha_beta = None
    tutorial.save()
    
    return redirect(tutorial.get_absolute_url_beta())

@can_write_and_read_now
@login_required
@require_POST
def ask_validation(request):
    '''User ask validation for his tutorial'''
    # Retrieve current tutorial;
    try:
        tutorial_pk = request.POST['tutorial']
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(Tutorial, pk = tutorial_pk)

    # If the user isn't an author of the tutorial or isn't in the staff,
    # he hasn't permission to execute this method:
    if request.user not in tutorial.authors.all():
        if not request.user.has_perm('forum.change_tutorial'):
            raise PermissionDenied

    # If 'pending' isn't in POST request, user don't would like validate
    # his tutorial and we redirect him to the tutorial.
    if not 'pending' in request.POST:
        redirect(tutorial.get_absolute_url())

    # We create and save validation object of the tutorial.
    validation = Validation()
    validation.tutorial = tutorial
    validation.date_proposition = datetime.now()
    validation.comment_authors = request.POST['comment']
    validation.version = request.POST['version']
    
    validation.save()
    
    validation.tutorial.sha_validation = request.POST['version']
    validation.tutorial.save()

    return redirect(tutorial.get_absolute_url())

@can_write_and_read_now
@login_required
@require_POST
def delete_tutorial(request):
    '''User would like delete his tutorial'''
    # Retrieve current tutorial;
    try:
        tutorial_pk = request.POST['tutorial']
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(Tutorial, pk = tutorial_pk)

    # If the user isn't an author of the tutorial or isn't in the staff,
    # he hasn't permission to execute this method:
    if request.user not in tutorial.authors.all():
        if not request.user.has_perm('forum.change_tutorial'):
            raise PermissionDenied

    # If 'delete' isn't in POST request, user don't would like delete
    # his tutorial and we redirect him to the tutorial.
    if not 'delete' in request.POST:
        redirect(tutorial.get_absolute_url())

    # Delete the tutorial on the repo and on the database.
    old_slug = os.path.join(settings.REPO_PATH, tutorial.slug)
    maj_repo_tuto(request,
                  old_slug_path=old_slug,
                  tuto = tutorial,
                  action = 'del')
    tutorial.delete()
    
    return redirect(reverse('zds.tutorial.views.index'))

@can_write_and_read_now
def modify_tutorial(request):
    if not request.method == 'POST':
        raise Http404

    tutorial_pk = request.POST['tutorial']
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

    # Validator actions
    if request.user.has_perm('tutorial.change_tutorial'):
        if 'valid-tuto' in request.POST:
            MEP(tutorial)
            validation = Validation.objects.filter(tutorial__pk=tutorial.pk, version = tutorial.sha_validation).all()[0]
            validation.comment_validator = request.POST['comment-v']
            validation.status = 'ACCEPT'
            validation.date_validation = datetime.now()
            validation.save()
            
            tutorial.sha_public = validation.version
            tutorial.sha_validation = ''
            tutorial.pubdate = datetime.now()
            tutorial.save()
            
            return redirect(tutorial.get_absolute_url())
        
        elif 'invalid-tuto' in request.POST:
            UNMEP(tutorial)
            validation = Validation.objects.get(tutorial__pk=tutorial.pk, version = tutorial.sha_public)
            validation.status = 'PENDING'
            validation.date_validation = None
            validation.save()
            
            tutorial.sha_validation = validation.version
            tutorial.sha_public = ''
            tutorial.pubdate = None
            tutorial.save()
            
            return redirect(tutorial.get_absolute_url())
    # User actions
    if request.user in tutorial.authors.all():
        if 'add_author' in request.POST:
            redirect_url = reverse('zds.tutorial.views.edit_tutorial') + \
                '?tutoriel={0}'.format(tutorial.pk)

            author_username = request.POST['author']
            author = None
            try:
                author = User.objects.get(username=author_username)
            except User.DoesNotExist:
                return redirect(redirect_url)

            tutorial.authors.add(author)
            tutorial.save()

            return redirect(redirect_url)

        elif 'remove_author' in request.POST:
            redirect_url = reverse('zds.tutorial.views.edit_tutorial') + \
                '?tutoriel={0}'.format(tutorial.pk)

            # Avoid orphan tutorials
            if tutorial.authors.all().count() <= 1:
                raise Http404

            author_pk = request.POST['author']
            author = get_object_or_404(User, pk=author_pk)

            tutorial.authors.remove(author)
            tutorial.save()

            return redirect(redirect_url)

    # No action performed, raise 404
    raise Http404

@can_read_now
@login_required
def view_tutorial(request, tutorial_pk, tutorial_slug):
    '''Show the given offline tutorial if exists'''
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

    # Only authors of the tutorial and staff can view tutorial in offline.
    if request.user not in tutorial.authors.all():
        if not request.user.has_perm('forum.change_tutorial'):
            raise PermissionDenied

    # Make sure the URL is well-formed
    if not tutorial_slug == slugify(tutorial.title):
        return redirect(tutorial.get_absolute_url())

    # Retrieve sha given by the user. This sha must to be exist.
    # If it doesn't exist, we take draft version of the article.
    try:
        sha = request.GET['version']
    except KeyError:
        sha = tutorial.sha_draft

    # Two variables to handle two distinct cases (large/small tutorial)
    chapter = None
    parts = None
    
    # Find the good manifest file
    repo = Repo(tutorial.get_path())

    # Load the tutorial.
    manifest = get_blob(repo.commit(sha).tree, 'manifest.json')
    mandata = json.loads(manifest)

    # If it's a small tutorial, fetch its chapter
    if tutorial.type == 'MINI':
        if 'chapter' in mandata:
            chapter = mandata['chapter']
            chapter['path'] = tutorial.get_path()
            chapter['type'] = 'MINI'
            chapter['intro'] = get_blob(repo.commit(sha).tree, 'introduction.md')
            chapter['conclu'] = get_blob(repo.commit(sha).tree, 'conclusion.md')
            cpt=1
            for ext in chapter['extracts'] :
                ext['position_in_chapter'] = cpt
                ext['path'] = tutorial.get_path()
                ext['txt'] = get_blob(repo.commit(sha).tree, ext['text'])
                cpt+=1
        else:
            chapter = None
    
    # If it's a big tutorial, fetch parts.
    else:
        parts = mandata['parts']
        cpt_p=1
        for part in parts :
            part['tutorial'] = tutorial
            part['path'] = tutorial.get_path()
            part['slug'] = slugify(part['title'])
            part['position_in_tutorial'] = cpt_p
            part['intro'] = get_blob(repo.commit(sha).tree, part['introduction'])
            part['conclu'] = get_blob(repo.commit(sha).tree, part['conclusion'])

            cpt_c=1
            for chapter in part['chapters'] :
                chapter['part'] = part
                chapter['path'] = tutorial.get_path()
                chapter['slug'] = slugify(chapter['title'])
                chapter['type'] = 'BIG'
                chapter['position_in_part'] = cpt_c
                chapter['position_in_tutorial'] = cpt_c * cpt_p
                chapter['intro'] = get_blob(repo.commit(sha).tree, chapter['introduction'])
                chapter['conclu'] = get_blob(repo.commit(sha).tree, chapter['conclusion'])
                cpt_e=1
                for ext in chapter['extracts'] :
                    ext['chapter'] = chapter
                    ext['position_in_chapter'] = cpt_e
                    ext['path'] = tutorial.get_path()
                    ext['txt'] = get_blob(repo.commit(sha).tree, ext['text'])
                    cpt_e+=1
                cpt_c+=1
                
            cpt_p+=1
    
    validation = Validation.objects.filter(tutorial__pk=tutorial.pk, version = sha)

    return render_template('tutorial/view_tutorial.html', {
        'tutorial': tutorial, 
        'chapter': chapter, 
        'parts': parts, 
        'version':sha, 
        'validation': validation
    })

@can_read_now
def view_tutorial_online(request, tutorial_pk, tutorial_slug):
    '''Display a tutorial'''
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)
    
    # If the tutorial isn't online, we raise 404 error.
    if not tutorial.on_line:
        raise Http404

    # Make sure the URL is well-formed
    if not tutorial_slug == slugify(tutorial.title):
        return redirect(tutorial.get_absolute_url())

    # Two variables to handle two distinct cases (large/small tutorial)
    chapter = None
    parts = None

    #find the good manifest file
    mandata = tutorial.load_json(online=True)

    # If it's a small tutorial, fetch its chapter
    if tutorial.type == 'MINI':
        if 'chapter' in mandata:
            chapter = mandata['chapter']
            chapter['path'] = tutorial.get_prod_path()
            chapter['type'] = 'MINI'
            intro = open(os.path.join(tutorial.get_prod_path(), mandata['introduction']+'.html'), "r")
            chapter['intro'] = intro.read()
            intro.close()
            conclu = open(os.path.join(tutorial.get_prod_path(), mandata['conclusion']+'.html'), "r")
            chapter['conclu'] = conclu.read()
            conclu.close()
            cpt=1
            for ext in chapter['extracts'] :
                ext['position_in_chapter'] = cpt
                ext['path'] = tutorial.get_prod_path()
                text = open(os.path.join(tutorial.get_prod_path(), ext['text']+'.html'), "r")
                ext['txt'] = text.read()
                text.close()
                cpt+=1
        else:
            chapter = None
        #chapter = Chapter.objects.get(tutorial=tutorial)
        
    else:
        parts = mandata['parts']
        cpt_p=1
        for part in parts :
            part['tutorial'] = tutorial
            part['path'] = tutorial.get_path()
            part['slug'] = slugify(part['title'])
            part['position_in_tutorial'] = cpt_p
            intro = open(os.path.join(tutorial.get_prod_path(), part['introduction']+'.html'), "r")
            part['intro'] = intro.read()
            intro.close()
            conclu = open(os.path.join(tutorial.get_prod_path(), part['conclusion']+'.html'), "r")
            part['conclu'] = conclu.read()
            conclu.close()

            cpt_c=1
            for chapter in part['chapters'] :
                chapter['part'] = part
                chapter['path'] = tutorial.get_path()
                chapter['slug'] = slugify(chapter['title'])
                chapter['type'] = 'BIG'
                chapter['position_in_part'] = cpt_c
                chapter['position_in_tutorial'] = cpt_c * cpt_p
                intro = open(os.path.join(tutorial.get_prod_path(), chapter['introduction']+'.html'), "r")
                chapter['intro'] = intro.read()
                intro.close()
                conclu = open(os.path.join(tutorial.get_prod_path(), chapter['conclusion']+'.html'), "r")
                chapter['conclu'] = conclu.read()
                cpt_e=1
                for ext in chapter['extracts'] :
                    ext['chapter'] = chapter
                    ext['position_in_chapter'] = cpt_e
                    ext['path'] = tutorial.get_path()
                    text = open(os.path.join(tutorial.get_prod_path(), ext['text']+'.html'), "r")
                    ext['txt'] = text.read()
                    text.close()
                    cpt_e+=1
                cpt_c+=1
                
            cpt_p+=1
    
    # If the user is authenticated
    if request.user.is_authenticated():
        # If the user is never read, we mark this tutorial read.
        if never_read(tutorial):
            mark_read(tutorial)
    
    # Find all notes of the tutorial.
    notes = Note.objects\
                .filter(tutorial__pk=tutorial.pk)\
                .order_by('position')\
                .all()
    
    # Retrieve pk of the last note. If there aren't notes
    # for the tutorial, we initialize this last note at 0.
    last_note_pk = 0
    if tutorial.last_note:
        last_note_pk = tutorial.last_note.pk
    
    # Handle pagination
    paginator = Paginator(notes, settings.POSTS_PER_PAGE)

    try:
        page_nbr = int(request.GET['page'])
    except KeyError:
        page_nbr = 1

    try:
        notes = paginator.page(page_nbr)
    except PageNotAnInteger:
        notes = paginator.page(1)
    except EmptyPage:
        raise Http404

    res = []
    if page_nbr != 1:
        # Show the last note of the previous page
        last_page = paginator.page(page_nbr - 1).object_list
        last_note = (last_page)[len(last_page) - 1]
        res.append(last_note)

    for note in notes:
        res.append(note)
        
    return render_template('tutorial/view_tutorial_online.html', {
        'tutorial': tutorial, 
        'chapter': chapter, 
        'parts': parts,
        'notes': res,
        'pages': paginator_range(page_nbr, paginator.num_pages),
        'nb': page_nbr,
        'last_note_pk': last_note_pk 
    })

@can_write_and_read_now
@login_required
def add_tutorial(request):
    ''''Adds a tutorial'''
    if request.method == 'POST':
        form = TutorialForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.data
            # Creating a tutorial
            tutorial = Tutorial()
            tutorial.title = data['title']
            tutorial.description = data['description']
            tutorial.type = data['type']
            tutorial.introduction = 'introduction.md'
            tutorial.conclusion = 'conclusion.md'
            tutorial.images = 'images'
            
            if 'licence' in data and data['licence']!= '' :
                lc = Licence.objects.filter(pk=data['licence']).all()[0]
                tutorial.licence = lc
            
            # add create date
            tutorial.create_at = datetime.now()
            tutorial.pubdate = datetime.now()
            
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
            
            tutorial.gallery = gal
            
            # Create image
            if 'image' in request.FILES:
                img = Image()
                img.physical = request.FILES['image']
                img.gallery = gal
                img.title = request.FILES['image']
                img.slug = slugify(request.FILES['image'])
                img.pubdate = datetime.now()
                img.save()
                tutorial.image = img
            
            tutorial.save()
            
            # Add subcategories on tutorial
            for subcat in form.cleaned_data['subcategory']:
                tutorial.subcategory.add(subcat)
            
            # We need to save the tutorial before changing its author list
            # since it's a many-to-many relationship
            tutorial.authors.add(request.user)
                
            # If it's a small tutorial, create its corresponding chapter
            if tutorial.type == 'MINI':
                chapter = Chapter()
                chapter.tutorial = tutorial
                chapter.save()
            
            tutorial.save()
            
            maj_repo_tuto(request,
                          new_slug_path=tutorial.get_path(), 
                          tuto = tutorial,
                          introduction=data['introduction'], 
                          conclusion=data['conclusion'],
                          action = 'add')
            
            return redirect(tutorial.get_absolute_url())
    else:
        form = TutorialForm()

    return render_template('tutorial/new_tutorial.html', {
        'form': form
    })

@can_write_and_read_now
@login_required
def edit_tutorial(request):
    '''Edit a tutorial'''
    # Retrieve current tutorial;
    try:
        tutorial_pk = request.GET['tutoriel']
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

    # If the user isn't an author of the tutorial or isn't in the staff,
    # he hasn't permission to execute this method:
    if request.user not in tutorial.authors.all():
        if not request.user.has_perm('forum.change_tutorial'):
            raise PermissionDenied

    if request.method == 'POST':
        form = TutorialForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.data
            old_slug = tutorial.get_path()
            tutorial.title = data['title']
            tutorial.description = data['description']
            
            if 'licence' in data and data['licence']!= '' :
                lc = Licence.objects.filter(pk=data['licence']).all()[0]
                tutorial.licence = lc
            
            # add MAJ date
            tutorial.update = datetime.now()
            
            # MAJ image
            if 'image' in request.FILES:
                img = Image()
                img.physical = request.FILES['image']
                img.gallery = tutorial.gallery
                img.title = request.FILES['image']
                img.slug = slugify(request.FILES['image'])
                img.pubdate = datetime.now()
                img.save()
                tutorial.image = img
            
            new_slug = os.path.join(settings.REPO_PATH, slugify(data['title']))
            
            tutorial.save()
            
            maj_repo_tuto(request,
                          old_slug_path=old_slug, 
                          new_slug_path=new_slug, 
                          tuto=tutorial, 
                          introduction=data['introduction'], 
                          conclusion=data['conclusion'],
                          action = 'maj')
            
            tutorial.subcategory.clear()
            for subcat in form.cleaned_data['subcategory']:
                tutorial.subcategory.add(subcat)
            
            tutorial.save()
            
            return redirect(tutorial.get_absolute_url())
    else:
        json = tutorial.load_json()
        if 'licence' in json:
            licence=Licence.objects.filter(code=json['licence']).all()[0]
        else:
            licence=None
            
        form = TutorialForm({
            'title': json['title'],
            'licence': licence,
            'description': json['description'],
            'subcategory': tutorial.subcategory.all(),
            'introduction': tutorial.get_introduction(),
            'conclusion': tutorial.get_conclusion(),
        })

    return render_template('tutorial/edit_tutorial.html', {
        'tutorial': tutorial, 'form': form
    })

# Part
@can_read_now
@login_required
def view_part(request, tutorial_pk, tutorial_slug, part_slug):
    '''Display a part'''
    
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)
    try:
        sha = request.GET['version']
    except KeyError:
        sha = tutorial.sha_draft
    
    beta = tutorial.in_beta() and sha == tutorial.sha_beta
    
    if (not request.user.has_perm('forum.change_tutorial'))\
       and (request.user not in tutorial.authors.all())\
       and not beta :
        raise Http404
    
    final_part = None
    #find the good manifest file
    repo = Repo(tutorial.get_path())

    manifest = get_blob(repo.commit(sha).tree, 'manifest.json')
    mandata = json.loads(manifest)
    
    parts = mandata['parts']
    cpt_p=1
    for part in parts :
        if part_slug == slugify(part['title']):
            part['tutorial'] = tutorial
            part['path'] = tutorial.get_path()
            part['slug'] = slugify(part['title'])
            part['position_in_tutorial'] = cpt_p
            part['intro'] = get_blob(repo.commit(sha).tree, part['introduction'])
            part['conclu'] = get_blob(repo.commit(sha).tree, part['conclusion'])    
    
            cpt_c=1
            for chapter in part['chapters'] :
                chapter['part'] = part
                chapter['path'] = tutorial.get_path()
                chapter['slug'] = slugify(chapter['title'])
                chapter['type'] = 'BIG'
                chapter['position_in_part'] = cpt_c
                chapter['position_in_tutorial'] = cpt_c * cpt_p
                chapter['intro'] = get_blob(repo.commit(sha).tree, chapter['introduction'])
                chapter['conclu'] = get_blob(repo.commit(sha).tree, chapter['conclusion'])
                cpt_e=1
                for ext in chapter['extracts'] :
                    ext['chapter'] = chapter
                    ext['position_in_chapter'] = cpt_e
                    ext['path'] = tutorial.get_path()
                    ext['txt'] = get_blob(repo.commit(sha).tree, ext['text'])
                    cpt_e+=1
                cpt_c+=1
                
            final_part = part
            break
        cpt_p+=1

    return render_template('tutorial/view_part.html', {
        'tutorial': tutorial,
        'part': final_part, 
        'version':sha
    })

@can_read_now
def view_part_online(request, tutorial_pk, tutorial_slug, part_slug):
    '''Display a part'''
    part = get_object_or_404(Part,
                             slug=part_slug, tutorial__pk=tutorial_pk)

    tutorial = part.tutorial
    if not tutorial.on_line :
        raise Http404

    # Make sure the URL is well-formed
    if not tutorial_slug == slugify(tutorial.title)\
            or not part_slug == slugify(part.title):
        return redirect(part.get_absolute_url())
    
    final_part = None
    #find the good manifest file
    mandata = tutorial.load_json()
    
    parts = mandata['parts']
    cpt_p=1
    for part in parts :
        if part_slug == slugify(part['title']):
            part['tutorial'] = tutorial
            part['path'] = tutorial.get_path()
            part['slug'] = slugify(part['title'])
            part['position_in_tutorial'] = cpt_p
            intro = open(os.path.join(tutorial.get_prod_path(), part['introduction']+'.html'), "r")
            part['intro'] = intro.read()
            intro.close()
            conclu = open(os.path.join(tutorial.get_prod_path(), part['conclusion']+'.html'), "r")
            part['conclu'] = conclu.read()
            conclu.close()
                
            cpt_c=1
            for chapter in part['chapters'] :
                chapter['part'] = part
                chapter['path'] = tutorial.get_path()
                chapter['slug'] = slugify(chapter['title'])
                chapter['type'] = 'BIG'
                chapter['position_in_part'] = cpt_c
                chapter['position_in_tutorial'] = cpt_c * cpt_p
                intro = open(os.path.join(tutorial.get_prod_path(), chapter['introduction']+'.html'), "r")
                chapter['intro'] = intro.read()
                intro.close()
                conclu = open(os.path.join(tutorial.get_prod_path(), chapter['conclusion']+'.html'), "r")
                chapter['conclu'] = conclu.read()
                conclu.close()
                cpt_e=1
                for ext in chapter['extracts'] :
                    ext['chapter'] = chapter
                    ext['position_in_chapter'] = cpt_e
                    ext['path'] = tutorial.get_prod_path()
                    text = open(os.path.join(tutorial.get_prod_path(), ext['text']+'.html'), "r")
                    ext['txt'] = text.read()
                    text.close()
                    cpt_e+=1
                cpt_c+=1
                
            final_part = part
            break
        cpt_p+=1
        
    return render_template('tutorial/view_part_online.html', {
        'part': part
    })

@can_write_and_read_now
@login_required
def add_part(request):
    '''Add a new part'''
    try:
        tutorial_pk = request.GET['tutoriel']
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)
    # Make sure it's a big tutorial, just in case
    if not tutorial.type == 'BIG':
        raise Http404
    # Make sure the user belongs to the author list
    if not request.user in tutorial.authors.all():
        raise Http404
    if request.method == 'POST':
        form = PartForm(request.POST)
        if form.is_valid():
            data = form.data
            part = Part()
            part.tutorial = tutorial
            part.title = data['title']
            part.position_in_tutorial = tutorial.get_parts().count() + 1
            
            new_slug = os.path.join(os.path.join(settings.REPO_PATH, part.tutorial.slug), slugify(data['title']))
            part.introduction = os.path.join(new_slug, 'introduction.md')
            part.conclusion = os.path.join(new_slug, 'conclusion.md')
            
            part.save()
            
            maj_repo_part(request,
                          new_slug_path =new_slug, 
                          part = part, 
                          introduction = data['introduction'], 
                          conclusion = data['conclusion'],
                          action = 'add')
            
            return redirect(part.get_absolute_url())
    else:
        form = PartForm()
    return render_template('tutorial/new_part.html', {
        'tutorial': tutorial, 'form': form
    })

@can_write_and_read_now
@login_required
def modify_part(request):
    '''Modifiy the given part'''
    if not request.method == 'POST':
        raise Http404

    part_pk = request.POST['part']
    part = get_object_or_404(Part, pk=part_pk)

    # Make sure the user is allowed to do that
    if not request.user in part.tutorial.authors.all():
        raise Http404

    if 'move' in request.POST:
        try:
            new_pos = int(request.POST['move_target'])
        # Invalid conversion, maybe the user played with the move button
        except ValueError:
            return redirect(part.tutorial.get_absolute_url())

        move(part, new_pos, 'position_in_tutorial', 'tutorial', 'get_parts')
        part.save()

    elif 'delete' in request.POST:
        # Delete all chapters belonging to the part
        Chapter.objects.all().filter(part=part).delete()

        # Move other parts
        old_pos = part.position_in_tutorial
        for tut_p in part.tutorial.get_parts():
            if old_pos <= tut_p.position_in_tutorial:
                tut_p.position_in_tutorial = tut_p.position_in_tutorial - 1
                tut_p.save()
        old_slug = os.path.join(os.path.join(settings.REPO_PATH, part.tutorial.slug), part.slug)
        
        
        maj_repo_part(request,
                          old_slug_path=old_slug,
                      action ='del')
        # Actually delete the part
        part.delete()

    return redirect(part.tutorial.get_absolute_url())

@can_write_and_read_now
@login_required
def edit_part(request):
    '''Edit the given part'''
    try:
        part_pk = int(request.GET['partie'])
    except KeyError:
        raise Http404
    
    part = get_object_or_404(Part, pk=part_pk)

    # Make sure the user is allowed to do that
    if not request.user in part.tutorial.authors.all():
        raise Http404
    
    if request.method == 'POST':
        form = PartForm(request.POST)
        if form.is_valid():
            data = form.data
            
            # Update title and his slug.
            part.title = data['title']
            new_slug = os.path.join(os.path.join(settings.REPO_PATH, part.tutorial.slug), slugify(data['title']))
            old_slug = part.get_path()

            # Update path for introduction and conclusion.
            part.introduction = os.path.join(new_slug, 'introduction.md')
            part.conclusion = os.path.join(new_slug, 'conclusion.md')
            
            part.save()

            maj_repo_part(request,
                          old_slug_path = old_slug, 
                          new_slug_path = new_slug, 
                          part = part, 
                          introduction = data['introduction'], 
                          conclusion = data['conclusion'],
                          action = 'maj')
            
            return redirect(part.get_absolute_url())
    else:
            
        form = PartForm({
            'title': part.title,
            'introduction' : part.get_introduction(),
            'conclusion' : part.get_conclusion(),
        })

    return render_template('tutorial/edit_part.html', {
        'part': part, 'form': form
    })


# Chapter
@can_read_now
@login_required
def view_chapter(request, tutorial_pk, tutorial_slug, part_slug,
                 chapter_slug):
    '''View chapter'''

    chapter = get_object_or_404(Chapter,
                                slug=chapter_slug,
                                part__slug=part_slug,
                                part__tutorial__pk=tutorial_pk)
    try:
        sha = request.GET['version']
    except KeyError:
        sha = None

    tutorial = chapter.get_tutorial()
    beta = tutorial.in_beta() and sha == tutorial.sha_beta
    
    if (not request.user.has_perm('forum.change_tutorial'))\
       and (request.user not in tutorial.authors.all())\
       and not beta :
        raise Http404

    if not tutorial_slug == slugify(tutorial.title)\
        or not part_slug == slugify(chapter.part.title)\
            or not chapter_slug == slugify(chapter.title):
        return redirect(chapter.get_absolute_url())
    
    #find the good manifest file
    repo = Repo(tutorial.get_path())

    manifest = get_blob(repo.commit(sha).tree, 'manifest.json')
    mandata = json.loads(manifest)
    
    parts = mandata['parts']
    cpt_p=1
    
    final_chapter = None
    chapter_tab = []
    final_position = 0
    for part in parts :
        cpt_c=1
        part['slug'] = slugify(part['title'])
        part['get_absolute_url'] = reverse('zds.tutorial.views.view_part_online', args=[tutorial.pk,tutorial.slug,part['slug']])
        part['tutorial'] = tutorial
        for chapter in part['chapters'] :
            chapter['part'] = part
            chapter['path'] = tutorial.get_path()
            chapter['slug'] = slugify(chapter['title'])
            chapter['type'] = 'BIG'
            chapter['position_in_part'] = cpt_c
            chapter['position_in_tutorial'] = cpt_c * cpt_p
            chapter['intro'] = get_blob(repo.commit(sha).tree, chapter['introduction'])
            chapter['conclu'] = get_blob(repo.commit(sha).tree, chapter['conclusion'])
            chapter['get_absolute_url'] = part['get_absolute_url'] + '{0}/'.format(chapter['slug'])
            cpt_e=1
            for ext in chapter['extracts'] :
                ext['chapter'] = chapter
                ext['position_in_chapter'] = cpt_e
                ext['path'] = tutorial.get_path()
                ext['txt'] = get_blob(repo.commit(sha).tree, ext['text'])
                cpt_e+=1
            chapter_tab.append(chapter)    
            if chapter_slug == slugify(chapter['title']):
                final_chapter = chapter
                final_position = len(chapter_tab)-1
            cpt_c+=1
        cpt_p+=1
        
    prev_chapter = chapter_tab[final_position-1] if final_position>0 else None
    next_chapter = chapter_tab[final_position+1] if final_position+1<len(chapter_tab) else None
    
    return render_template('tutorial/view_chapter.html', {
        'chapter': final_chapter,
        'prev': prev_chapter,
        'next': next_chapter, 
        'version':sha
    })

@can_read_now
def view_chapter_online(request, tutorial_pk, tutorial_slug, part_slug,
                 chapter_slug):
    '''View chapter'''

    chapter_bd = get_object_or_404(Chapter,
                                slug=chapter_slug,
                                part__slug=part_slug,
                                part__tutorial__pk=tutorial_pk)

    tutorial = chapter_bd.get_tutorial()
    if not tutorial.on_line :
        raise Http404

    if not tutorial_slug == slugify(tutorial.title)\
        or not part_slug == slugify(chapter_bd.part.title)\
            or not chapter_slug == slugify(chapter_bd.title):
        return redirect(chapter_bd.get_absolute_url())

    #find the good manifest file
    mandata = tutorial.load_json()
    
    parts = mandata['parts']
    cpt_p=1
    
    final_chapter = None
    chapter_tab = []
    final_position = 0
    for part in parts :
        cpt_c=1
        part['slug'] = slugify(part['title'])
        part['get_absolute_url_online'] = reverse('zds.tutorial.views.view_part_online', args=[tutorial.pk,tutorial.slug,part['slug']])
        part['tutorial'] = tutorial
        for chapter in part['chapters'] :
            chapter['part'] = part
            chapter['path'] = tutorial.get_path()
            chapter['slug'] = slugify(chapter['title'])
            chapter['type'] = 'BIG'
            chapter['position_in_part'] = cpt_c
            chapter['position_in_tutorial'] = cpt_c * cpt_p
            intro = open(os.path.join(tutorial.get_prod_path(), chapter['introduction']+'.html'), "r")
            chapter['intro'] = intro.read()
            intro.close()
            conclu = open(os.path.join(tutorial.get_prod_path(), chapter['conclusion']+'.html'), "r")
            chapter['conclu'] = conclu.read()
            chapter['get_absolute_url_online'] = part['get_absolute_url_online'] + '{0}/'.format(chapter['slug'])
            conclu.close()
            cpt_e=1
            for ext in chapter['extracts'] :
                ext['chapter'] = chapter
                ext['position_in_chapter'] = cpt_e
                ext['path'] = tutorial.get_path()
                text = open(os.path.join(tutorial.get_prod_path(), ext['text']+'.html'), "r")
                ext['txt'] = text.read()
                text.close()
                cpt_e+=1
            chapter_tab.append(chapter)    
            if chapter_slug == slugify(chapter['title']):
                final_chapter = chapter
                final_position = len(chapter_tab)-1
            cpt_c+=1
        cpt_p+=1
        
    prev_chapter = chapter_tab[final_position-1] if final_position>0 else None
    next_chapter = chapter_tab[final_position+1] if final_position+1<len(chapter_tab) else None

    return render_template('tutorial/view_chapter_online.html', {
        'chapter': final_chapter,
        'prev': prev_chapter,
        'next': next_chapter
    })

@can_write_and_read_now
@login_required
def add_chapter(request):
    '''Add a new chapter to given part'''
    try:
        part_pk = request.GET['partie']
    except KeyError:
        raise Http404
    part = get_object_or_404(Part, pk=part_pk)

    # Make sure the user is allowed to do that
    if not request.user in part.tutorial.authors.all():
        raise Http404

    if request.method == 'POST':
        form = ChapterForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.data

            # We check that another chapter doesn't exist with the same slug
            already_exist = False
            for p_chapter in part.get_chapters():
                if p_chapter.slug == slugify(data['title']):
                    already_exist = True
                    break

            if not already_exist:
                chapter = Chapter()
                chapter.title = data['title']
                chapter.part = part
                chapter.position_in_part = part.get_chapters().count() + 1
                chapter.update_position_in_tutorial()
                # Create image
                if 'image' in request.FILES:
                    img = Image()
                    img.physical = request.FILES['image']
                    img.gallery = gal
                    img.title = request.FILES['image']
                    img.slug = slugify(request.FILES['image'])
                    img.pubdate = datetime.now()
                    img.save()
                    chapter.image = img
                
                if chapter.tutorial:
                    chapter_path = os.path.join(os.path.join(settings.REPO_PATH, chapter.tutorial.slug), chapter.slug)
                    chapter.introduction = os.path.join(chapter.slug, 'introduction.md')
                    chapter.conclusion = os.path.join(chapter.slug, 'conclusion.md')
                else:
                    chapter_path = os.path.join(os.path.join(os.path.join(settings.REPO_PATH, chapter.part.tutorial.slug), chapter.part.slug), chapter.slug)
                    chapter.introduction = os.path.join(os.path.join(chapter.part.tutorial.slug, chapter.slug), 'introduction.md')
                    chapter.conclusion = os.path.join(os.path.join(chapter.part.tutorial.slug, chapter.slug), 'conclusion.md')
                new_slug = os.path.join(chapter_path , slugify(data['title']))
                
                chapter.save()
                
                maj_repo_chapter(request,
                                 new_slug_path=new_slug, 
                                 chapter=chapter, 
                                 introduction=data['introduction'], 
                                 conclusion=data['conclusion'],
                                 action='add')
                
                

                if 'submit_continue' in request.POST:
                    form = ChapterForm()
                    messages.success(request,
                                     u'Chapitre « {0} » ajouté avec succès.'
                                     .format(chapter.title))
                else:
                    return redirect(chapter.get_absolute_url())
            else:
                messages.error(request, u'Un chapitre portant le même nom '
                                        u'existe déjà dans cette partie.')
    else:
        form = ChapterForm()

    return render_template('tutorial/new_chapter.html', {
        'part': part, 'form': form
    })

@can_write_and_read_now
@login_required
def modify_chapter(request):
    '''Modify the given chapter'''
    if not request.method == 'POST':
        raise Http404
    data = request.POST
    try:
        chapter_pk = request.POST['chapter']
    except KeyError:
        raise Http404
    chapter = get_object_or_404(Chapter, pk=chapter_pk)

    # Make sure the user is allowed to do that
    if not request.user in chapter.get_tutorial().authors.all():
        raise Http404

    if 'move' in data:
        try:
            new_pos = int(request.POST['move_target'])
        # User misplayed with the move button
        except ValueError:
            return redirect(chapter.get_absolute_url())

        move(chapter, new_pos, 'position_in_part', 'part', 'get_chapters')
        chapter.update_position_in_tutorial()
        chapter.save()

        messages.info(request, u'Le chapitre a bien été déplacé.')

    elif 'delete' in data:
        old_pos = chapter.position_in_part
        old_tut_pos = chapter.position_in_tutorial
        # Move other chapters first
        for tut_c in chapter.part.get_chapters():
            if old_pos <= tut_c.position_in_part:
                tut_c.position_in_part = tut_c.position_in_part - 1
                tut_c.save()
        
        maj_repo_chapter(request,
                         new_slug_path=chapter.get_path(),
                         action = 'del')
        # Then delete the chapter
        chapter.delete()
        # Update all the position_in_tutorial fields for the next chapters
        for tut_c in Chapter.objects\
                .filter(position_in_tutorial__gt=old_tut_pos):
            tut_c.update_position_in_tutorial()
            tut_c.save()

        messages.info(request, u'Le chapitre a bien été supprimé.')

        return redirect(chapter.part.get_absolute_url())

    return redirect(chapter.get_absolute_url())

@can_write_and_read_now
@login_required
def edit_chapter(request):
    '''Edit the given chapter'''

    try:
        chapter_pk = int(request.GET['chapitre'])
    except KeyError:
        raise Http404
    
    chapter = get_object_or_404(Chapter, pk=chapter_pk)
    big = chapter.part
    small = chapter.tutorial
    
    # Make sure the user is allowed to do that
    if big and (not request.user in chapter.part.tutorial.authors.all())\
            or small and (not request.user in chapter.tutorial.authors.all()):
        raise Http404

    if request.method == 'POST':

        if chapter.part:
            form = ChapterForm(request.POST, request.FILES)
        else:
            form = EmbdedChapterForm(request.POST, request.FILES)

        if form.is_valid():
            data = form.data
            if chapter.part:
                if chapter.tutorial:
                    new_slug = os.path.join(os.path.join(settings.REPO_PATH, chapter.tutorial.slug), slugify(data['title']))
                else:
                    new_slug = os.path.join(os.path.join(os.path.join(settings.REPO_PATH, chapter.part.tutorial.slug), chapter.part.slug), slugify(data['title']))
                    
                chapter.title = data['title']
                # Create image
                if 'image' in request.FILES:
                    img = Image()
                    img.physical = request.FILES['image']
                    img.gallery = gal
                    img.title = request.FILES['image']
                    img.slug = slugify(request.FILES['image'])
                    img.pubdate = datetime.now()
                    img.save()
                    chapter.image = img
            old_slug = chapter.get_path()
            
            chapter.save()
            
            maj_repo_chapter(request,
                             old_slug_path = old_slug,
                             new_slug_path = new_slug, 
                             chapter=chapter,
                             introduction=data['introduction'], 
                             conclusion=data['conclusion'],
                             action = 'maj')
            
            
            return redirect(chapter.get_absolute_url())
    else:
        if chapter.part:
            form = ChapterForm({
                'title': chapter.title,
                'introduction': chapter.get_introduction(),
                'conclusion': chapter.get_conclusion(),
            })
        else:
            form = EmbdedChapterForm({
                'introduction': chapter.get_introduction(),
                'conclusion': chapter.get_conclusion()
            })

    return render_template('tutorial/edit_chapter.html', {
        'chapter': chapter, 'form': form
    })


# Extract
@can_read_now
@login_required
def add_extract(request):
    '''Add extract'''

    try:
        chapter_pk = int(request.GET['chapitre'])
    except KeyError:
        raise Http404
    chapter = get_object_or_404(Chapter, pk=chapter_pk)

    notify = None

    if request.method == 'POST':
        form = ExtractForm(request.POST)
        if form.is_valid():
            data = form.data
            extract = Extract()
            extract.chapter = chapter
            extract.position_in_chapter = chapter.get_extract_count() + 1
            extract.title = data['title']
            
            extract.text = extract.get_path(relative=True)
            extract.save()
            
            maj_repo_extract(request,
                             new_slug_path=extract.get_path(), 
                             extract=extract, 
                             text=data['text'],
                             action='add')
            

            if 'submit_continue' in request.POST:
                form = ExtractForm()
                messages.success(
                    request, u'Extrait « {0} » ajouté avec succès.'
                    .format(extract.title))
            else:
                return redirect(extract.get_absolute_url())
    else:
        form = ExtractForm()

    return render_template('tutorial/new_extract.html', {
        'chapter': chapter, 'form': form, 'notify': notify
    })

@can_write_and_read_now
@login_required
def edit_extract(request):
    '''Edit extract'''

    try:
        extract_pk = request.GET['extrait']
    except KeyError:
        raise Http404

    extract = get_object_or_404(Extract, pk=extract_pk)
    
    b = extract.chapter.part
    if b and (not request.user in extract.chapter.part.tutorial.authors.all())\
            or not b and (not request.user in
                          extract.chapter.tutorial.authors.all()):
        raise Http404

    if request.method == 'POST':
        form = ExtractForm(request.POST)
        if form.is_valid():
            data = form.data
            old_slug = extract.get_path()
            
            extract.title = data['title']
            extract.text = extract.get_path(relative=True)
            
            if extract.chapter.tutorial:
                chapter_part = os.path.join(os.path.join(settings.REPO_PATH, extract.chapter.tutorial.slug), extract.chapter.slug)
            else:
                chapter_part = os.path.join(os.path.join(os.path.join(settings.REPO_PATH, extract.chapter.part.tutorial.slug), extract.chapter.part.slug), extract.chapter.slug)
            new_slug = os.path.join(chapter_part, slugify(data['title'])+'.md')
            
            extract.save()
            
            maj_repo_extract(request,
                             old_slug_path=old_slug, 
                             new_slug_path=new_slug, 
                             extract=extract, 
                             text=data['text'],
                             action = 'maj')
            
            
            return redirect(extract.get_absolute_url())
    else:
        form = ExtractForm({
            'title': extract.title,
            'text': extract.get_text(),
        })

    return render_template('tutorial/edit_extract.html', {
        'extract': extract, 'form': form
    })

@can_write_and_read_now
def modify_extract(request):
    if not request.method == 'POST':
        raise Http404

    data = request.POST

    try:
        extract_pk = request.POST['extract']
    except KeyError:
        raise Http404

    extract = get_object_or_404(Extract, pk=extract_pk)
    chapter = extract.chapter

    if 'delete' in data:
        old_pos = extract.position_in_chapter
        for extract_c in extract.chapter.get_extracts():
            if old_pos <= extract_c.position_in_chapter:
                extract_c.position_in_chapter = extract_c.position_in_chapter \
                    - 1
                extract_c.save()

        if extract.chapter.tutorial:
            chapter_path = os.path.join(os.path.join(settings.REPO_PATH, extract.chapter.tutorial.slug), extract.chapter.slug)
        else:
            chapter_path = os.path.join(os.path.join(os.path.join(settings.REPO_PATH, extract.chapter.part.tutorial.slug), extract.chapter.part.slug), extract.chapter.slug)
        old_slug = os.path.join(chapter_path, slugify(extract.title)+'.md')
        
        maj_repo_extract(request,
                         old_slug_path=old_slug, 
                         extract=extract,
                         action = 'del')
        
        extract.delete()
        return redirect(chapter.get_absolute_url())

    elif 'move' in data:
        try:
            new_pos = int(request.POST['move_target'])
        # Error, the user misplayed with the move button
        except ValueError:
            return redirect(extract.get_absolute_url())

        move(extract, new_pos, 'position_in_chapter', 'chapter',
             'get_extracts')
        extract.save()

        return redirect(extract.get_absolute_url())

    raise Http404

@can_read_now
def find_tuto(request, pk_user):
    try:
        type = request.GET['type']
    except KeyError:
        type = None
        
    u = get_object_or_404(User, pk=pk_user)
    if type == 'beta':
        tutos = Tutorial.objects.all().filter(authors__in=[u], sha_beta__isnull=False)\
                              .order_by('-pubdate')
        
        return render_template('tutorial/find_betatutorial.html', {
            'tutos': tutos, 'usr':u,
        })
    else:
        tutos = Tutorial.objects.all().filter(authors__in=[u], sha_public__isnull=False)\
                              .order_by('-pubdate')
    
        return render_template('tutorial/find_tutorial.html', {
            'tutos': tutos, 'usr':u,
        })

def upload_images(request, tutorial):
    mapping = OrderedDict()
    #download images 
    if 'images' in request.FILES :
        zfile = zipfile.ZipFile(request.FILES['images'])
        for i in zfile.namelist():
            ph = os.path.join(settings.MEDIA_ROOT,"tutorial", str(tutorial.pk), i)
            ph_temp = os.path.join(tutorial.get_path(), i)
            try:
                data = zfile.read(i)
                fp = open(ph_temp, "wb")
                fp.write(data)
                fp.close()
                f = File(open(os.path.join(tutorial.get_path(), i),'r'))
                pic = Image()
                pic.gallery = tutorial.gallery
                pic.physical.save(ph, f, save = True)
                
                mapping[i]=pic.physical.url
                
            except IOError: 
                try: os.makedirs(ph_temp)
                except: pass

        zfile.close()
    return mapping

def replace_real_url(md_text, dict):
    for dt_old, dt_new in dict.iteritems():
        md_text=md_text.replace(dt_old, dt_new)
    
    return md_text

@can_write_and_read_now
@login_required
def import_tuto(request):
    if request.method == 'POST':
        form = ImportForm(request.POST, request.FILES)
        # check extension
        if 'file' in request.FILES :
            filename = str(request.FILES['file'])
            ext = filename.split('.')[-1]
            if ext == 'tuto':
                if form.is_valid():
                    
                    tutorial = Tutorial()
                        
                    # add create date
                    tutorial.create_at = datetime.now()
                    
                    
                    tree = etree.parse(request.FILES['file'])
                    racine_big = tree.xpath("/bigtuto")
                    racine_mini = tree.xpath("/minituto")
                    if(len(racine_big) > 0):
                        # it's a big tuto
                        tutorial.type = 'BIG'
                        tutorial_title = tree.xpath("/bigtuto/titre")[0]
                        tutorial_intro = tree.xpath("/bigtuto/introduction")[0]
                        tutorial_conclu = tree.xpath("/bigtuto/conclusion")[0]
                        
                        
                        tutorial.title = tutorial_title.text.strip()
                        tutorial.description = tutorial_title.text.strip()
                        tutorial.images = 'images'
                        tutorial.introduction = 'introduction.md'
                        tutorial.conclusion = 'conclusion.md'
                        # Creating the gallery
                        gal = Gallery()
                        gal.title = tutorial_title.text
                        gal.slug = slugify(tutorial_title.text)
                        gal.pubdate = datetime.now()
                        gal.save()
                        
                        # Attach user to gallery
                        userg = UserGallery()
                        userg.gallery = gal
                        userg.mode = 'W'  # write mode
                        userg.user = request.user
                        userg.save()
            
                        tutorial.gallery = gal
                        
                        tuto_path = os.path.join(settings.REPO_PATH, slugify(tutorial.title))
                        
                        tutorial.save()
                        
                        mapping = upload_images(request, tutorial)
                        
                        maj_repo_tuto(request,
                                      new_slug_path=tuto_path, 
                                      tuto=tutorial, 
                                      introduction= replace_real_url(tutorial_intro.text, mapping), 
                                      conclusion= replace_real_url(tutorial_conclu.text, mapping),
                                      action = 'add')
                        
                        
                        
                        tutorial.authors.add(request.user)
                        part_count = 1
                        for partie in tree.xpath("/bigtuto/parties/partie"):
                            part_title = tree.xpath("/bigtuto/parties/partie[" + str(part_count) + "]/titre")[0]
                            part_intro = tree.xpath("/bigtuto/parties/partie[" + str(part_count) + "]/introduction")[0]
                            part_conclu = tree.xpath("/bigtuto/parties/partie[" + str(part_count) + "]/conclusion")[0]
                            
                            part = Part()
                            part.title = part_title.text.strip()
                            part.position_in_tutorial = part_count
                            
                            part.tutorial = tutorial
                            
                            part.introduction = os.path.join(slugify(part_title.text.strip()),'introduction.md')
                            part.conclusion = os.path.join(slugify(part_title.text.strip()),'conclusion.md')
                            
                            part_path = os.path.join(os.path.join(settings.REPO_PATH, part.tutorial.slug), slugify(part.title))
                            
                            part.save()
                            
                            maj_repo_part(request, None, part_path, part, replace_real_url(part_intro.text, mapping), replace_real_url(part_conclu.text, mapping), action='add')
                            
                            
                            chapter_count = 1
                            for chapitre in tree.xpath("/bigtuto/parties/partie[" + str(part_count) + "]/chapitres/chapitre"):
                                chapter_title = tree.xpath("/bigtuto/parties/partie[" + str(part_count) + "]/chapitres/chapitre[" + str(chapter_count) + "]/titre")[0]
                                chapter_intro = tree.xpath("/bigtuto/parties/partie[" + str(part_count) + "]/chapitres/chapitre[" + str(chapter_count) + "]/introduction")[0]
                                chapter_conclu = tree.xpath("/bigtuto/parties/partie[" + str(part_count) + "]/chapitres/chapitre[" + str(chapter_count) + "]/conclusion")[0]
                                
                                chapter = Chapter()
                                chapter.title = chapter_title.text.strip()
                                chapter.position_in_part = chapter_count
                                chapter.position_in_tutorial = part_count * chapter_count
                                chapter.part = part
                                
                                chapter.introduction = os.path.join(part.slug,os.path.join(slugify(chapter_title.text.strip()),'introduction.md'))
                                chapter.conclusion = os.path.join(part.slug,os.path.join(slugify(chapter_title.text.strip()),'conclusion.md'))  
                                
                                chapter_path = os.path.join(os.path.join(os.path.join(settings.REPO_PATH, chapter.part.tutorial.slug), chapter.part.slug), slugify(chapter.title))
                                
                                chapter.save()
                                
                                maj_repo_chapter(request,
                                                 new_slug_path=chapter_path, 
                                                 chapter=chapter, 
                                                 introduction= replace_real_url(chapter_intro.text, mapping), 
                                                 conclusion= replace_real_url(chapter_conclu.text, mapping),
                                                 action='add')
                                
                                
                                extract_count = 1
                                for souspartie in tree.xpath("/bigtuto/parties/partie[" + str(part_count) + "]/chapitres/chapitre[" + str(chapter_count) + "]/sousparties/souspartie"):
                                    extract_title = tree.xpath("/bigtuto/parties/partie[" + str(part_count) + "]/chapitres/chapitre[" + str(chapter_count) + "]/sousparties/souspartie[" + str(extract_count) + "]/titre")[0]
                                    extract_text = tree.xpath("/bigtuto/parties/partie[" + str(part_count) + "]/chapitres/chapitre[" + str(chapter_count) + "]/sousparties/souspartie[" + str(extract_count) + "]/texte")[0]
                                    
                                    extract = Extract()
                                    extract.title = extract_title.text.strip()
                                    extract.position_in_chapter = extract_count
                                    extract.chapter = chapter
                                    
                                    extract.text = extract.get_path(relative=True)
                                    extract.save()

                                    maj_repo_extract(request,new_slug_path=extract.get_path(), extract=extract, text=replace_real_url(extract_text.text, mapping), action= 'add')
                                    
                                    
                                    extract_count += 1
                                    
                                chapter_count += 1

                            part_count += 1
                    elif len(racine_mini) > 0 :
                        # it's a mini tuto
                        tutorial.type = 'MINI'
                        tutorial_title = tree.xpath("/minituto/titre")[0]
                        tutorial_intro = tree.xpath("/minituto/introduction")[0]
                        tutorial_conclu = tree.xpath("/minituto/conclusion")[0]
                        
                        tutorial.title = tutorial_title.text.strip()
                        tutorial.description = tutorial_title.text.strip()
                        tutorial.images = 'images'
                        tutorial.introduction = 'introduction.md'
                        tutorial.conclusion = 'conclusion.md'
                        
                        # Creating the gallery
                        gal = Gallery()
                        gal.title = tutorial_title.text
                        gal.slug = slugify(tutorial_title.text)
                        gal.pubdate = datetime.now()
                        gal.save()
                        
                        # Attach user to gallery
                        userg = UserGallery()
                        userg.gallery = gal
                        userg.mode = 'W'  # write mode
                        userg.user = request.user
                        userg.save()
            
                        tutorial.gallery = gal
                        
                        tuto_path = os.path.join(settings.REPO_PATH, slugify(tutorial.title))
                        
                        tutorial.save()
                        
                        mapping = upload_images(request, tutorial)
                        
                        maj_repo_tuto(request,
                                      new_slug_path=tuto_path, 
                                      tuto=tutorial, 
                                      introduction= replace_real_url(tutorial_intro.text, mapping), 
                                      conclusion= replace_real_url(tutorial_conclu.text, mapping),
                                      action = 'add')
                        
                        tutorial.authors.add(request.user)
                        
                        chapter = Chapter()
                        chapter.tutorial = tutorial
                        chapter.save()
                        
                        extract_count = 1
                        for souspartie in tree.xpath("/minituto/sousparties/souspartie"):
                            extract_title = tree.xpath("/minituto/sousparties/souspartie[" + str(extract_count) + "]/titre")[0]
                            extract_text = tree.xpath("/minituto/sousparties/souspartie[" + str(extract_count) + "]/texte")[0]
                            
                            extract = Extract()
                            extract.title = extract_title.text.strip()
                            extract.position_in_chapter = extract_count
                            extract.chapter = chapter
                            extract.text = extract.get_path(relative=True)
                            
                            extract.save()
                            
                            maj_repo_extract(request,new_slug_path=extract.get_path(), extract=extract, text=replace_real_url(extract_text.text, mapping), action='add')
                            
                            
                            extract_count += 1
                    
                    return redirect(tutorial.get_absolute_url())
            else: 
                raise Http404
                 
    else:
        form = ImportForm()
    
    return render_template('tutorial/import_tutorial.html', {
        'form': form
    })

# Handling deprecated links

def deprecated_view_tutorial_redirect(request, tutorial_pk, tutorial_slug):
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)
    return redirect(tutorial.get_absolute_url(), permanent=True)


def deprecated_view_part_redirect(request, tutorial_pk, tutorial_slug,
                                  part_pos, part_slug):
    part = Part.objects.get(
        position_in_tutorial=part_pos, tutorial__pk=tutorial_pk)
    return redirect(part.get_absolute_url(), permanent=True)


def deprecated_view_chapter_redirect(
    request, tutorial_pk, tutorial_slug, part_pos, part_slug,
        chapter_pos, chapter_slug):
    chapter = Chapter.objects.get(position_in_part=chapter_pos,
                                  part__position_in_tutorial=part_pos,
                                  part__tutorial__pk=tutorial_pk)
    return redirect(chapter.get_absolute_url(), permanent=True)


# Handling repo

def maj_repo_tuto(request, old_slug_path=None, new_slug_path=None, tuto=None, introduction=None, conclusion=None, action=None):
    
    if action == 'del' :
        shutil.rmtree(old_slug_path)
    else:
        if action == 'maj':    
            shutil.move(old_slug_path, new_slug_path)
            repo = Repo(new_slug_path)
            msg='Modification du tutoriel'
        elif action == 'add' :
            if not os.path.exists(new_slug_path) : os.makedirs(new_slug_path, mode=0777)
            repo = Repo.init(new_slug_path, bare=False)
            msg='Creation du tutoriel'
        
        repo = Repo(new_slug_path)
        index = repo.index
        
        man_path=os.path.join(new_slug_path,'manifest.json')
        tuto.dump_json(path=man_path)
        index.add(['manifest.json'])
        
        
        intro = open(os.path.join(new_slug_path, 'introduction.md'), "w")
        intro.write(smart_str(introduction).strip())
        intro.close()
        index.add(['introduction.md'])
    
        conclu = open(os.path.join(new_slug_path, 'conclusion.md'), "w")
        conclu.write(smart_str(conclusion).strip())
        conclu.close()
        index.add(['conclusion.md'])
        
        aut_user = str(request.user.pk)
        aut_email = str(request.user.email)
        if aut_email is None or aut_email.strip() == "":
            aut_email ="inconnu@zestedesavoir.com"
            
        com = index.commit(msg.encode('utf-8'),
                           author=Actor(aut_user, aut_email),
                           committer=Actor(aut_user, aut_email))
        tuto.sha_draft=com.hexsha
        tuto.save()
        
    
def maj_repo_part(request, old_slug_path=None, new_slug_path=None, part=None, introduction=None, conclusion=None, action=None):
    
    repo = Repo(part.tutorial.get_path())
    index = repo.index
    
    msg='repo partie'
    if action == 'del' :
        shutil.rmtree(old_slug_path)
        msg='Suppresion de la partie '
        index.remove([part.get_path(relative=True)])
        
    else:
        if action == 'maj' :
            os.rename(old_slug_path, new_slug_path)
            msg='Modification de la partie '
        elif action == 'add' :
            if not os.path.exists(new_slug_path) : os.makedirs(new_slug_path, mode=0777)
            msg='Creation de la partie '
        
        index.add([slugify(part.title)])
        
        man_path=os.path.join(part.tutorial.get_path(),'manifest.json')
        part.tutorial.dump_json(path=man_path)
        index.add(['manifest.json'])
        
        intro = open(os.path.join(new_slug_path, 'introduction.md'), "w")
        intro.write(smart_str(introduction).strip())
        intro.close()
        index.add([os.path.join(part.get_path(relative=True),'introduction.md')])
    
        conclu = open(os.path.join(new_slug_path, 'conclusion.md'), "w")
        conclu.write(smart_str(conclusion).strip())
        conclu.close()
        index.add([os.path.join(part.get_path(relative=True),'conclusion.md')])
    
    aut_user = str(request.user.pk)
    aut_email = str(request.user.email)
    if aut_email is None or aut_email.strip() == "":
        aut_email ="inconnu@zestedesavoir.com"
    com_part = index.commit(msg.encode('utf-8'),
                           author=Actor(aut_user, aut_email),
                           committer=Actor(aut_user, aut_email))
    part.tutorial.sha_draft=com_part.hexsha
    part.tutorial.save()
    
    part.save()
        
def maj_repo_chapter(request, old_slug_path=None, new_slug_path=None, chapter=None, introduction=None, conclusion=None, action=None):
    if(chapter.tutorial):
        repo = Repo(os.path.join(settings.REPO_PATH, chapter.tutorial.slug))
        ph=chapter.slug
    else:
        repo = Repo(os.path.join(settings.REPO_PATH, chapter.part.tutorial.slug))
        ph=os.path.join(chapter.part.slug, slugify(chapter.title))
        
    index = repo.index
    msg='repo chapitre'
    
    if action == 'del' :
        shutil.rmtree(old_slug_path)
        msg='Suppresion du chapitre  '
        index.remove([ph])
    else:
        if action == 'maj' :
            os.rename(old_slug_path, new_slug_path)
            msg='Modification du chapitre '
        elif action == 'add' :
            if not os.path.exists(new_slug_path) : os.makedirs(new_slug_path, mode=0777)
            msg='Creation du chapitre '

        
        intro = open(os.path.join(new_slug_path, 'introduction.md'), "w")
        intro.write(smart_str(introduction).strip())
        intro.close()
    
        conclu = open(os.path.join(new_slug_path, 'conclusion.md'), "w")
        conclu.write(smart_str(conclusion).strip())
        conclu.close()
        
        index.add([ph])
    
    #update manifest
    if(chapter.tutorial):
        man_path=os.path.join(chapter.tutorial.get_path(),'manifest.json')
        chapter.tutorial.dump_json(path=man_path)
    else:
        man_path=os.path.join(chapter.part.tutorial.get_path(),'manifest.json')
        chapter.part.tutorial.dump_json(path=man_path)
    
    index.add(['manifest.json'])

    aut_user = str(request.user.pk)
    aut_email = str(request.user.email)
    if aut_email is None or aut_email.strip() == "":
        aut_email ="inconnu@zestedesavoir.com"
    com_ch = index.commit(msg.encode('utf-8'),
                           author=Actor(aut_user, aut_email),
                           committer=Actor(aut_user, aut_email))
    
    if(chapter.tutorial):
        chapter.tutorial.sha_draft=com_ch.hexsha
        chapter.tutorial.save()
    else:
        chapter.part.tutorial.sha_draft=com_ch.hexsha
        chapter.part.tutorial.save()
    
    chapter.save()
    
def maj_repo_extract(request, old_slug_path=None, new_slug_path=None, extract=None, text=None, action=None):
    if(extract.chapter.tutorial):
        repo = Repo(os.path.join(settings.REPO_PATH, extract.chapter.tutorial.slug))
        ph=extract.chapter.slug
    else:
        repo = Repo(os.path.join(settings.REPO_PATH, extract.chapter.part.tutorial.slug))
        ph=os.path.join(extract.chapter.part.slug, slugify(extract.chapter.title))

    index = repo.index
    
    if action == 'del' :
         os.remove(old_slug_path)
         msg='Suppression de l\'exrait '
    else:        
        if action == 'maj' :
            os.rename(old_slug_path, new_slug_path)
            msg='Modification de l\'exrait '
        ext = open(new_slug_path, "w")
        ext.write(smart_str(text).strip())
        ext.close()
        index.add([extract.get_path(relative=True)])
        msg='Mise a jour de l\'exrait '
    
    #update manifest
    if(extract.chapter.tutorial):
        man_path=os.path.join(extract.chapter.tutorial.get_path(),'manifest.json')
        extract.chapter.tutorial.dump_json(path=man_path)
    else:
        man_path=os.path.join(extract.chapter.part.tutorial.get_path(),'manifest.json')
        extract.chapter.part.tutorial.dump_json(path=man_path)
        
    index.add(['manifest.json'])
    
    aut_user = str(request.user.pk)
    aut_email = str(request.user.email)
    if aut_email is None or aut_email.strip() == "":
        aut_email ="inconnu@zestedesavoir.com"
    com_ex = index.commit(msg.encode('utf-8'),
                           author=Actor(aut_user, aut_email),
                           committer=Actor(aut_user, aut_email))
    
    if(extract.chapter.tutorial):
        extract.chapter.tutorial.sha_draft = com_ex.hexsha
        extract.chapter.tutorial.save()
    else:
        extract.chapter.part.tutorial.sha_draft = com_ex.hexsha
        extract.chapter.part.tutorial.save()
        
    extract.save()


@can_read_now
def download(request):
    '''Download a tutorial'''

    tutorial = get_object_or_404(Tutorial, pk=request.GET['tutoriel'])

    ph=os.path.join(settings.REPO_PATH, tutorial.slug)
    repo = Repo(ph)
    repo.archive(open(ph+".tar",'w'))
    
    response = HttpResponse(open(ph+".tar", 'rb').read(), mimetype='application/tar')
    response['Content-Disposition'] = 'attachment; filename={0}.tar'.format(tutorial.slug)

    return response

@can_read_now
@permission_required('tutorial.change_tutorial', raise_exception=True)
def download_markdown(request):
    '''Download a markdown tutorial'''

    tutorial = get_object_or_404(Tutorial, pk=request.GET['tutoriel'])
    
    response = HttpResponse(open(os.path.join(tutorial.get_prod_path(), tutorial.slug+'.md'), "rb").read(), mimetype='application/txt')
    response['Content-Disposition'] = 'attachment; filename={0}.md'.format(tutorial.slug)

    return response
    
@can_read_now
def download_pdf(request):
    '''Download a pdf tutorial'''

    tutorial = get_object_or_404(Tutorial, pk=request.GET['tutoriel'])
    
    response = HttpResponse(open(os.path.join(tutorial.get_prod_path(), tutorial.slug+'.pdf'), "rb").read(), mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename={0}.pdf'.format(tutorial.slug)

    return response

@can_read_now
def download_epub(request):
    '''Download an epub tutorial'''

    tutorial = get_object_or_404(Tutorial, pk=request.GET['tutoriel'])
    
    response = HttpResponse(open(os.path.join(tutorial.get_prod_path(), tutorial.slug+'.epub'), "rb").read(), mimetype='application/epub')
    response['Content-Disposition'] = 'attachment; filename={0}.epub'.format(tutorial.slug)
    
    return response
    
def get_url_images(md_text, pt):
    regex = ur"(!\[.*?\]\()(.+?)(\))"
    imgs = re.findall(regex, md_text)
    
    for img in imgs:
        parse_object = urlparse(img[1])
        
        if parse_object.scheme in ('http', 'https'):
            (filepath, filename) = os.path.split(parse_object.path)
            urlretrieve(img[1], os.path.join(pt, img[1]))
            ext = filename.split('.')[-1]
            if ext == 'gif':
                im = ImagePIL.open(os.path.join(pt, img[1]))
                im.save(os.path.join(pt, filename.split('.')[0]+'.png'))
        else :
            srcfile = settings.SITE_ROOT + img[1]
            dstroot = pt + img[1]
            dstdir =  os.path.dirname(dstroot)

            if not os.path.exists(dstdir) : os.makedirs(dstdir)
            shutil.copy(srcfile, dstroot)
            
            ext = dstroot.split('.')[-1]
            if ext == 'gif':
                im = ImagePIL.open(dstroot)
                im.save(os.path.join(dstroot.split('.')[0]+'.png'))
        

def sub(g):
    start = g.group('start')
    url = g.group('url')
    parse_object = urlparse(url)
    (filepath, filename) = os.path.split(parse_object.path)
    ext = filename.split('.')[-1]
    if ext == 'gif':
        if parse_object.scheme in ('http', 'https'):
            url = os.path.join ("images", filename.split('.')[0]+'.png')
        else:
            url = url.split('.')[0][1:]+'.png'
    else :
        url = url[1:]

    end = g.group('end')
    return start + url + end

def markdown_to_out(md_text):
    return re.sub(r'(?P<start>!\[.*?\]\()(?P<url>.+?)(?P<end>\))', sub, md_text)
                    
def MEP(tutorial):
    if os.path.isdir(tutorial.get_prod_path()):
        shutil.rmtree(tutorial.get_prod_path())
        
    shutil.copytree(tutorial.get_path(), tutorial.get_prod_path())
    
    #create resources directory
    
    #convert markdown file to html file
    fichiers=[] 
    for root, dirs, files in os.walk(tutorial.get_prod_path()): 
        for i in files: 
            fichiers.append(os.path.join(root, i))
    
    for fichier in fichiers:
        ext = fichier.split('.')[-1]
        if ext == 'md':
            md_file = open(fichier, "r")
            md_file_contenu = md_file.read()
            md_file.close()
            
            #download images
            get_url_images(md_file_contenu.decode('utf-8'), tutorial.get_prod_path())
            
            #convert to out format
            out_file = open(fichier, "w")
            out_file.write(markdown_to_out(md_file_contenu))
            out_file.close()
            
            html_file = open(fichier+'.html', "w")
            html_file.write(emarkdown(md_file_contenu.decode('utf-8')))
            html_file.close()
            
            
    
    #load markdown out
    contenu = export_tutorial_to_md(tutorial)
    
    out_file = open(os.path.join(tutorial.get_prod_path(), tutorial.slug+'.md'), "w")
    out_file.write(smart_str(contenu).replace('°', 'o').replace('−','-'))
    out_file.close()
    
    #load pandoc
    os.chdir(tutorial.get_prod_path())
    os.system("pandoc -s -S --toc "+os.path.join(tutorial.get_prod_path(), tutorial.slug)+".md -o "+os.path.join(tutorial.get_prod_path(), tutorial.slug)+".pdf")
    os.system("pandoc -s -S --toc "+os.path.join(tutorial.get_prod_path(), tutorial.slug)+".md -o "+os.path.join(tutorial.get_prod_path(), tutorial.slug)+".epub")
    os.chdir(settings.SITE_ROOT)

def UNMEP(tutorial):
    if os.path.isdir(tutorial.get_prod_path()):
        shutil.rmtree(tutorial.get_prod_path())

@can_write_and_read_now
@login_required
def answer(request):
    '''
    Adds an answer from a user to an tutorial
    '''
    try:
        tutorial_pk = request.GET['tutorial']
    except KeyError:
        raise Http404
    
    g_tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)
    
    notes = Note.objects.filter(tutorial=g_tutorial).order_by('-pubdate')[:3]
    
    if g_tutorial.last_note:
        last_note_pk = g_tutorial.last_note.pk
    else:
        last_note_pk=0

    # Making sure noteing is allowed
    if g_tutorial.is_locked:
        raise Http404

    # Check that the user isn't spamming
    if g_tutorial.antispam(request.user):
        raise Http404

    # If we just sent data
    if request.method == 'POST':
        data = request.POST
        newnote = last_note_pk != int(data['last_note'])

        # Using the « preview button », the « more » button or new note
        if 'preview' in data or 'more' in data or newnote:
            return render_template('tutorial/answer.html', {
                'text': data['text'], 'tutorial': g_tutorial, 'notes': notes,
                'last_note_pk': last_note_pk, 'newnote': newnote
            })

        # Saving the message
        else:
            form = NoteForm(request.POST)
            if form.is_valid() and data['text'].strip() !='':
                data = form.data

                note = Note()
                note.tutorial = g_tutorial
                note.author = request.user
                note.text = data['text']
                note.text_html = emarkdown(data['text'])
                note.pubdate = datetime.now()
                note.position = g_tutorial.get_note_count() + 1
                note.ip_address = get_client_ip(request)
                note.save()

                g_tutorial.last_note = note
                g_tutorial.save()

                return redirect(note.get_absolute_url())
            else:
                raise Http404

    else:
        text = ''

        # Using the quote button
        if 'cite' in request.GET:
            note_cite_pk = request.GET['cite']
            note_cite = Note.objects.get(pk=note_cite_pk)

            for line in note_cite.text.splitlines():
                text = text + '> ' + line + '\n'

            text = u'**{0} a écrit :**\n{1}\n'.format(
                note_cite.author.username, text)

        return render_template('tutorial/answer.html', {
            'tutorial': g_tutorial, 'text': text, 'notes': notes,
            'last_note_pk': last_note_pk
        })

@can_write_and_read_now
@login_required
def edit_note(request):
    '''
    Edit the given user's note
    '''
    
    try:
        note_pk = request.GET['message']
    except KeyError:
        raise Http404

    note = get_object_or_404(Note, pk=note_pk)

    g_tutorial = None
    if note.position >= 1:
        g_tutorial = get_object_or_404(Tutorial, pk=note.tutorial.pk)

    # Making sure the user is allowed to do that
    if note.author != request.user:
        if request.method == 'GET' and request.user.has_perm('tutorial.change_note'):
            messages.add_message(
                request, messages.WARNING,
                u'Vous éditez ce message en tant que modérateur (auteur : {}).'
                u' Soyez encore plus prudent lors de l\'édition de celui-ci !'
                .format(note.author.username))
            note.alerts.all().delete()

    if request.method == 'POST':
        
        if 'delete-note' in request.POST:
            if note.author == request.user or request.user.has_perm('tutorial.change_note'):
                note.alerts.all().delete()
                note.is_visible=False
                if request.user.has_perm('tutorial.change_note'):
                    note.text_hidden=request.POST['text_hidden']
                note.editor = request.user
            
        if 'show-note' in request.POST:
            if request.user.has_perm('tutorial.change_note'):
                note.is_visible=True
                note.text_hidden=''
                    
        if 'signal-note' in request.POST:
            if note.author != request.user :
                alert = Alert()
                alert.author = request.user
                alert.text=request.POST['signal-text']
                alert.pubdate = datetime.now()
                alert.save()
                note.alerts.add(alert)
        # Using the preview button
        if 'preview' in request.POST:
            return render_template('tutorial/edit_note.html', {
                'note': note, 'tutorial': g_tutorial, 'text': request.POST['text'],
            })
        
        if not 'delete-note' in request.POST and not 'signal-note' in request.POST and not 'show-note' in request.POST:
            # The user just sent data, handle them
            if request.POST['text'].strip() !='':
                note.text = request.POST['text']
                note.text_html = emarkdown(request.POST['text'])
                note.update = datetime.now()
                note.editor = request.user
        
        note.save()
        
        return redirect(note.get_absolute_url())

    else:
        return render_template('tutorial/edit_note.html', {
            'note': note, 'tutorial': g_tutorial, 'text': note.text
        })


@can_write_and_read_now
@login_required
def like_note(request):
    '''Like a note'''
    
    try:
        note_pk = request.GET['message']
    except KeyError:
        raise Http404

    resp = {}
    note = get_object_or_404(Note, pk=note_pk)
    user = request.user
    
    if note.author.pk != request.user.pk:
        # Making sure the user is allowed to do that
        if CommentLike.objects.filter(user__pk=user.pk, comments__pk=note_pk).count()==0:
            like=CommentLike()
            like.user=user
            like.comments=note
            note.like=note.like+1
            note.save()
            like.save()
            if CommentDislike.objects.filter(user__pk=user.pk, comments__pk=note_pk).count()>0:
                CommentDislike.objects.filter(user__pk=user.pk, comments__pk=note_pk).all().delete()
                note.dislike=note.dislike-1
                note.save()
        else:
            CommentLike.objects.filter(user__pk=user.pk, comments__pk=note_pk).all().delete()
            note.like=note.like-1
            note.save()
    
    resp['upvotes'] = note.like
    resp['downvotes'] = note.dislike
    
    if request.is_ajax():
        return HttpResponse(json.dumps(resp))
    else:
        return redirect(note.get_absolute_url())

@can_write_and_read_now
@login_required
def dislike_note(request):
    '''Dislike a note'''
    
    try:
        note_pk = request.GET['message']
    except KeyError:
        raise Http404

    note = get_object_or_404(Note, pk=note_pk)
    user = request.user

    if note.author.pk != request.user.pk:
        # Making sure the user is allowed to do that
        if CommentDislike.objects.filter(user__pk=user.pk, comments__pk=note_pk).count()==0:
            dislike=CommentDislike()
            dislike.user=user
            dislike.comments=note
            note.dislike=note.dislike+1
            note.save()
            dislike.save()
            if CommentLike.objects.filter(user__pk=user.pk, comments__pk=note_pk).count()>0:
                CommentLike.objects.filter(user__pk=user.pk, comments__pk=note_pk).all().delete()
                note.like=note.like-1
                note.save()
        else :
            CommentDislike.objects.filter(user__pk=user.pk, comments__pk=note_pk).all().delete()
            note.dislike=note.dislike-1
            note.save()

    return redirect(note.get_absolute_url())
