from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from django.urls import reverse
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from django.test import tag
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains

from zds.member.factories import StaffProfileFactory, ProfileFactory
from zds.tutorialv2.factories import (
    LicenceFactory,
    SubCategoryFactory,
    PublishableContentFactory,
    ContainerFactory,
    ExtractFactory,
)
from zds.tutorialv2.models.database import PublishedContent, PublishableContent
from zds.tutorialv2.tests import TutorialTestMixin, TutorialFrontMixin
from copy import deepcopy
from django.conf import settings
import os

from zds.utils.factories import CategoryFactory

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app['content']['repo_private_path'] = os.path.join(settings.BASE_DIR, 'contents-private-test')
overridden_zds_app['content']['repo_public_path'] = os.path.join(settings.BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overridden_zds_app)
@override_settings(ES_ENABLED=False)
@tag('front')
class PublicationFronttest(StaticLiveServerTestCase, TutorialTestMixin, TutorialFrontMixin):
    @classmethod
    def setUpClass(cls):
        super(PublicationFronttest, cls).setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(PublicationFronttest, cls).tearDownClass()

    def tearDown(self):
        super().tearDown()
        self.clean_media_dir()

    def setUp(self):
        self.overridden_zds_app = overridden_zds_app
        # don't build PDF to speed up the tests
        overridden_zds_app['content']['build_pdf_when_published'] = False

        self.staff = StaffProfileFactory().user

        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        overridden_zds_app['member']['bot_account'] = self.mas.username

        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory(category=CategoryFactory())

        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user
        self.content = PublishableContentFactory(author_list=[self.user_author], light=False)
        self.part_published = ContainerFactory(db_object=self.content, light=False, parent=self.content.load_version())
        self.ignored_part = ContainerFactory(db_object=self.content, light=False, parent=self.content.load_version())
        ExtractFactory(db_object=self.content, container=self.part_published, light=False)
        ExtractFactory(db_object=self.content, container=self.ignored_part, light=False)

    def test_partial_publication(self):
        self.login_author()
        self.selenium.get(self.live_server_url + self.ignored_part.get_absolute_url())
        find_element = self.selenium.find_element_by_css_selector
        button = WebDriverWait(self.selenium, 20).until(
            expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, '.readiness'))
        )
        readiness = button.get_attribute('data-is-ready')
        button.click()
        self.wait_element_attribute_change((By.CSS_SELECTOR, '.readiness'), 'data-is-ready', readiness, 20)
        self.content = PublishableContent.objects.get(pk=self.content.pk)
        self.ignored_part = self.content.load_version().children[1]
        self.assertFalse(self.ignored_part.ready_to_publish, 'part should be marked as not ready to publish')
        self.selenium.get(self.live_server_url + self.content.get_absolute_url())
        self.selenium.get(self.live_server_url + self.ignored_part.get_absolute_url())
        button = find_element('.readiness')
        self.assertNotEqual(
            readiness, button.get_attribute('data-is-ready'), 'part should be marked as not ready to publish'
        )
        self.selenium.get(self.live_server_url + self.content.get_absolute_url())
        self.ask_validation()
        self.logout()
        self.login_staff()
        self.take_reservation()
        self.validate()
        url = PublishedContent.objects.get(content__pk=self.content.pk).get_absolute_url_online()
        self.selenium.get(self.live_server_url + url)
        self.assertRaises(
            WebDriverException,
            find_element,
            'a[href="{}"]'.format(
                reverse(
                    'tutorial:view-container',
                    kwargs={'slug': self.content.slug, 'pk': self.content.pk, 'container_slug': self.ignored_part.slug},
                )
            ),
        )

    def test_collaborative_article_edition_and_editor_persistence(self):
        selenium = self.selenium
        find_element = selenium.find_element_by_css_selector

        author = ProfileFactory()

        article = PublishableContentFactory(type='ARTICLE', author_list=[author.user])

        versioned_article = article.load_version()
        article.sha_draft = versioned_article.repo_update('article', '', '', update_slug=False)
        article.save()

        article_edit_url = reverse('content:edit', args=[article.pk, article.slug])

        self.login(author)

        selenium.get(self.live_server_url + article_edit_url)

        intro = find_element('div#div_id_introduction div.CodeMirror')
        # ActionChains: Support for CodeMirror https://stackoverflow.com/a/48969245/2226755
        action_chains = ActionChains(selenium)
        scrollDriverTo(selenium, 0, 312)
        action_chains.click(intro).perform()
        action_chains.send_keys('intro').perform()

        output = 'div#div_id_introduction div.CodeMirror div.CodeMirror-code'
        self.assertEqual('intro', find_element(output).text)

        article.sha_draft = versioned_article.repo_update('article', 'new intro', '', update_slug=False)
        article.save()

        selenium.refresh()

        self.assertEqual('new intro', find_element('.md-editor#id_introduction').get_attribute('value'))

    def test_the_editor_forgets_its_content_on_form_submission(self):
        selenium = self.selenium
        find_element = selenium.find_element_by_css_selector

        author = ProfileFactory()

        self.login(author)
        new_article_url = self.live_server_url + reverse('content:create-article')
        selenium.get(new_article_url)
        WebDriverWait(self.selenium, 10).until(ec.element_to_be_clickable(
            (By.CSS_SELECTOR, 'input[type=checkbox][name=subcategory]')
        )).click()
        license_select = Select(find_element('#id_licence'))
        license_select.select_by_index(len(license_select.options) - 1)

        find_element('#id_title').send_keys('Oulipo')

        intro = find_element('div#div_id_introduction div.CodeMirror')
        action_chains = ActionChains(selenium)
        action_chains.click(intro).perform()
        action_chains.send_keys('Le cadavre exquis boira le vin nouveau.').perform()

        find_element('.content-container button[type=submit]').click()

        self.assertTrue(WebDriverWait(selenium, 10).until(ec.title_contains(('Oulipo'))))

        selenium.get(new_article_url)

        self.assertEqual('', find_element('.md-editor#id_introduction').get_attribute('value'))


def scrollDriverTo(driver, x, y):
    scriptScrollTo = 'window.scrollTo(%s, %s);' % (x, y)
    driver.execute_script(scriptScrollTo)
