from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from django.test import tag


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
        self.selenium.get('%s%s' % (self.live_server_url, '/'))
        self.assertEqual(
            'Zeste de Savoir',
            self.selenium.find_element_by_css_selector('p.copyright').text[:15]
        )
        self.assertEqual('Zeste de Savoir', self.selenium.title)

    def test_trigger_remember(self):
        self.selenium.get('%s%s'
                          % (self.live_server_url, '/membres/connexion/'))
        is_checked = self.selenium.find_element_by_id('id_remember').is_selected()
        self.selenium.find_element_by_id('id_remember').click()
        self.assertNotEqual(is_checked,
                            self.selenium.
                            find_element_by_id('id_remember').is_selected())
