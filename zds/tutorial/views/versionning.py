# -*- coding: utf-8 -*-
import os.path
import shutil
from django.utils.encoding import smart_str
from git import *
from zds.utils import slugify
from zds.utils.tutorials import get_blob, move
import json as json_writer
try:
    import ujson as json_reader
except:
    try:
        import simplejson as json_reader
    except:
        import json as json_reader


def maj_repo(user=None,
             old_slug_path=None,
             new_slug_path=None,
             contents=[],
             tutorial=None,
             obj=None,
             action=None):
    """
    Add any content in the git repository
    
    user : means instance of user queryset object
    old_slug_path : old path of content
    new_slug_path : new path of content which replace old path
    contents : list of tuple of relative path and content value
    tutorial : means tutorials instance of queryset object
    obj : means queryset object updated in the repository
    action : action can be "add", "maj", "del"

    Example for get introduction of chapter:
    
    get_content(obj_top=tutorial,
                level="chapter",
                obj_level=chapter,
                path_obj_fn="get_path",
                type="introduction",
                sha=sha)
    """

    if action == "del":
        if old_slug_path:
            if os.path.isfile(old_slug_path):
                os.remove(old_slug_path)
            else:
                shutil.rmtree(old_slug_path)
    else:
        if action == "maj":            
            if old_slug_path != new_slug_path:
                os.rename(old_slug_path, new_slug_path)
            repo = Repo(tutorial.get_path())
            msg = "Modification"
        elif action == "add":
            if not os.path.exists(new_slug_path):
                if new_slug_path[-2:]!="md":
                    os.makedirs(new_slug_path, mode=0o777)
            if obj==tutorial:
                repo = Repo.init(new_slug_path, bare=False)
            else:
                repo = Repo(tutorial.get_path())
            msg = "Creation"
        index = repo.index
        man_path = os.path.join(tutorial.get_path(), "manifest.json")
        tutorial.dump_json(path=man_path)
        update_files = [obj.get_path(relative=True)]
        update_files.append("manifest.json")
        for (f, content) in contents:
            if content is not None:
                cnt = open(os.path.join(tutorial.get_path(), f), "w")
                cnt.write(smart_str(content).strip())
                cnt.close()
                update_files.append(f)
        index.add(update_files)
        aut_user = str(user.pk)
        aut_email = str(user.email)
        if aut_email is None or aut_email.strip() == "":
            aut_email = "inconnu@zestedesavoir.com"
        com = index.commit(msg.encode("utf-8"),
                           author=Actor(aut_user, aut_email),
                           committer=Actor(aut_user, aut_email))
        tutorial.sha_draft = com.hexsha
        tutorial.save()
        obj.save()