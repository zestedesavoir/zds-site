# coding: utf-8

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.urlresolvers import reverse
from django.test import tag
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from zds.member.factories import ProfileFactory
from zds.utils.factories import CategoryFactory
from zds.tutorialv2.factories import PublishableContentFactory, SubCategoryFactory, \
    LicenceFactory


# NOTE In Django 1.11.4 there is a --selenium option for python manage.py test
@tag('front')
class MemberFrontTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super(MemberFrontTests, cls).setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(MemberFrontTests, cls).tearDownClass()

    def test_zestedesavoir_is_present(self):
        self.selenium.get(self.live_server_url + '/')
        self.assertEqual(
            'Zeste de Savoir',
            self.selenium.find_element_by_css_selector('p.copyright').text[:15]
        )
        self.assertEqual('Zeste de Savoir', self.selenium.title)

    def test_trigger_remember(self):
        self.selenium.get(self.live_server_url + reverse('member-login'))
        is_checked = self.selenium.find_element_by_id('id_remember').is_selected()
        self.selenium.find_element_by_id('id_remember').click()
        self.assertNotEqual(is_checked,
                            self.selenium
                            .find_element_by_id('id_remember').is_selected())

    def __login(self, profile):
        """
        TODO: This is definitely way too slow. Fasten this.
        """
        selenium = self.selenium
        find_element = selenium.find_element_by_css_selector

        selenium.get(self.live_server_url + reverse('member-login'))

        username = find_element('.content-container input#id_username')
        password = find_element('.content-container input#id_password')
        username.send_keys(profile.user.username)
        password.send_keys('hostel77')

        find_element('.content-container button[type=submit]').click()

        # Wait until the user is logged in (this raises if the element
        # is not found).
        find_element('.header-container .logbox .my-account .username')

    def test_collaborative_article_edition_and_editor_persistence(self):
        # TODO: Move this test elsewhere.

        selenium = self.selenium
        find_element = selenium.find_element_by_css_selector

        author = ProfileFactory()

        article = PublishableContentFactory(type='ARTICLE')
        article.authors.add(author.user)
        article.save()

        versioned_article = article.load_version()
        article.sha_draft = versioned_article.repo_update(
            'article', '', '', update_slug=False)
        article.save()

        article_edit_url = reverse('content:edit', args=[
            article.pk,
            article.slug,
        ])

        self.__login(author)

        selenium.get(self.live_server_url + article_edit_url)

        intro = find_element('.md-editor#id_introduction')
        intro.send_keys('intro')

        selenium.refresh()

        self.assertEqual(
            'intro',
            find_element('.md-editor#id_introduction').get_attribute('value'),
        )

        article.sha_draft = versioned_article.repo_update(
            'article', 'new intro', '', update_slug=False)
        article.save()

        selenium.refresh()

        self.assertEqual(
            'new intro',
            find_element('.md-editor#id_introduction').get_attribute('value'),
        )

    def test_the_editor_forgets_its_content_on_form_submission(self):
        # TODO: Move this test elsewhere.

        selenium = self.selenium
        find_element = selenium.find_element_by_css_selector

        cat = CategoryFactory()
        SubCategoryFactory(category=cat)

        LicenceFactory(code='CC BY')

        author = ProfileFactory()

        self.__login(author)

        new_article_url = self.live_server_url + reverse('content:create-article')
        selenium.get(new_article_url)

        find_element('input[type=checkbox][name=subcategory]').click()
        license_select = Select(find_element('#id_licence'))
        license_select.options[-1].click()

        find_element('#id_title').send_keys('Oulipo')

        intro = find_element('.md-editor#id_introduction')
        intro.send_keys('Le cadavre exquis boira le vin nouveau.')

        find_element('.content-container button[type=submit]').click()

        self.assertTrue(
            WebDriverWait(selenium, 10).until(ec.title_contains(('Oulipo')))
        )

        selenium.get(new_article_url)

        self.assertEqual(
            '',
            find_element('.md-editor#id_introduction').get_attribute('value'),
        )
