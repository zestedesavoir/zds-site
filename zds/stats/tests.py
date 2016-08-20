# coding: utf-8
from datetime import datetime, timedelta

from django.core.management import call_command
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from oauth2_provider.models import Application, AccessToken
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.test import APIClient

from zds.stats.factories import LogFactory
from zds.stats.models import Log, Source, City, Country, Device, Browser, OS
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishedContentFactory, LicenceFactory
from zds.gallery.factories import UserGalleryFactory, ImageFactory, GalleryFactory
import tempfile
import os
import shutil
from zds.settings import BASE_DIR


overrided_drf = settings.REST_FRAMEWORK
overrided_drf["PAGINATE_BY"] = 3

overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')

type_content_tutorial = "tutoriel"
type_content_article = "article"


def create_public_big_tutorial(client, type_content, author, licence, validator):

    pubdate = datetime.now() - timedelta(days=1)
    bigtuto = PublishedContentFactory(type=type_content, author_list=[author])
    public_version = bigtuto.public_version
    public_version.publication_date = pubdate
    public_version.save()
    bigtuto.gallery = GalleryFactory()
    bigtuto.licence = licence
    UserGalleryFactory(gallery=bigtuto.gallery, user=author, mode='W')
    bigtuto.save()

    client.login(
        username=validator.username,
        password='hostel77')

    return bigtuto

def generate_public_content(client, type_content, number, author, licence, validator, sources=None, uagents=None, ips=None):
    f = tempfile.NamedTemporaryFile()
    for i in range(number):
        source = None
        uagent = None
        ip = None
        if sources is not None:
            source = sources[i % len(sources)]
        if uagents is not None:
            uagent = uagents[i % len(uagents)]
        if ips is not None:
            ip = ips[i % len(ips)]
        bigtuto = create_public_big_tutorial(client=client, type_content=type_content, author=author, licence=licence, validator=validator)
        log = LogFactory(type_content=type_content, pk=bigtuto.pk, source=source, uagent=uagent, ip=ip)
        f.write("{}\n".format(log))

    f.seek(0)
    opts = {}
    call_command('parse_logs', f.name, **opts)
    f.close()



@override_settings(REST_FRAMEWORK=overrided_drf)
@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class ContentEmptyListAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        settings.ZDS_APP['content']['build_pdf_when_published'] = False

    def test_list_of_contents_empty(self):
        all_type = [type_content_tutorial, type_content_article]
        for type_c in all_type:
            response = self.client.get(reverse('api:stats:list-content-visits', args=[type_c]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('count'), 0)
            self.assertEqual(response.data.get('results'), [])
            self.assertIsNone(response.data.get('next'))
            self.assertIsNone(response.data.get('previous'))

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

        settings.ZDS_APP['content']['build_pdf_when_published'] = True


@override_settings(REST_FRAMEWORK=overrided_drf)
@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class ContentListAPITest(APITestCase):

    def setUp(self):
        settings.ZDS_APP['content']['build_pdf_when_published'] = False
        self.client = APIClient()
        self.licence = LicenceFactory()
        self.author = ProfileFactory().user
        self.validator = StaffProfileFactory().user
        self.sources_data = ["http://www.google.fr","http://www.zestedesavoir.com"]
        self.uagents_data = ["Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0", "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.13"]
        self.ips_data = ["81.7.15.115","142.4.213.25"] # first : None, Germany | second : Montréal, Canada

        for type_c in ["TUTORIAL", "ARTICLE"]:
            generate_public_content(client=self.client,
                type_content=type_c,
                licence=self.licence,
                author=self.author,
                validator=self.validator,
                number = overrided_drf["PAGINATE_BY"],
                sources = self.sources_data,
                uagents = self.uagents_data,
                ips = self.ips_data
                )
        

    def test_list_of_contents(self):

        all_type = [type_content_tutorial, type_content_article]
        for type_c in all_type:
            # list of contents visits
            response = self.client.get(reverse('api:stats:list-content-visits', args=[type_c]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('count'), overrided_drf["PAGINATE_BY"])
            self.assertEqual(len(response.data.get('results')), overrided_drf["PAGINATE_BY"])
            self.assertIsNone(response.data.get('next'))
            self.assertIsNone(response.data.get('previous'))
            # list of contents source visits
            response = self.client.get(reverse('api:stats:list-source-content-visits', args=[type_c]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('count'), len(self.sources_data))
            self.assertEqual(len(response.data.get('results')), len(self.sources_data)) 
            self.assertIsNone(response.data.get('next'))
            self.assertIsNone(response.data.get('previous'))
            # list of tutotials city
            response = self.client.get(reverse('api:stats:list-city-content-visits', args=[type_c]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('count'), 1)
            self.assertEqual(len(response.data.get('results')), 1)
            self.assertIsNone(response.data.get('next'))
            self.assertIsNone(response.data.get('previous'))
            # list of tutotials country
            response = self.client.get(reverse('api:stats:list-country-content-visits', args=[type_c]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('count'), 2)
            self.assertEqual(len(response.data.get('results')), 2)
            self.assertIsNone(response.data.get('next'))
            self.assertIsNone(response.data.get('previous'))
            # list of tutotials device
            response = self.client.get(reverse('api:stats:list-device-content-visits', args=[type_c]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('count'), 1)
            self.assertEqual(len(response.data.get('results')), 1)
            self.assertIsNone(response.data.get('next'))
            self.assertIsNone(response.data.get('previous'))
            # list of tutotials os
            response = self.client.get(reverse('api:stats:list-os-content-visits', args=[type_c]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('count'), 2)
            self.assertEqual(len(response.data.get('results')), 2)
            self.assertIsNone(response.data.get('next'))
            self.assertIsNone(response.data.get('previous'))
            # list of tutotials browser
            response = self.client.get(reverse('api:stats:list-browser-content-visits', args=[type_c]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data.get('count'), 2)
            self.assertEqual(len(response.data.get('results')), 2)
            self.assertIsNone(response.data.get('next'))
            self.assertIsNone(response.data.get('previous'))

    def test_logs_generate(self):
        f = tempfile.NamedTemporaryFile()
        opts = {"lines": 10, "path": f.name}
        call_command('generate_logs', "", **opts)

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

        settings.ZDS_APP['content']['build_pdf_when_published'] = True