# coding: utf-8

# NOTE : this file is only there for tests purpose, it will be deleted in final version

import os

from django.test import TestCase
from django.test.utils import override_settings
from zds.settings import SITE_ROOT

from zds.tutorialv2.models import Container, Extract, VersionedContent


@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(REPO_PATH=os.path.join(SITE_ROOT, 'tutoriels-private-test'))
@override_settings(REPO_PATH_PROD=os.path.join(SITE_ROOT, 'tutoriels-public-test'))
@override_settings(REPO_ARTICLE_PATH=os.path.join(SITE_ROOT, 'articles-data-test'))
class ContentTests(TestCase):

    def setUp(self):
        self.start_version = 'ca5508a'  # real version, adapt it !
        self.content = VersionedContent(self.start_version, 1, 'TUTORIAL', 'Mon tutoriel no1')

        self.container = Container(1, 'Mon chapitre no1')
        self.content.add_container(self.container)

        self.extract = Extract(1, 'Un premier extrait')
        self.container.add_extract(self.extract)
        self.content.update_children()

    def test_workflow_content(self):
        print(self.container.position_in_parent)
