from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from django.urls import reverse
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options


@tag("front")
class MemberFrontTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super(MemberFrontTests, cls).setUpClass()
        options = Options()
        options.headless = True
        cls.selenium = Firefox(options=options)
        cls.selenium.implicitly_wait(30)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(MemberFrontTests, cls).tearDownClass()

    def test_zestedesavoir_is_present(self):
        self.selenium.get(self.live_server_url + "/")
        self.assertEqual("Zeste de Savoir", self.selenium.find_element_by_css_selector("p.copyright").text[:15])
        self.assertEqual("Zeste de Savoir", self.selenium.title)

    def test_trigger_remember(self):
        self.selenium.get(self.live_server_url + reverse("member-login"))
        is_checked = self.selenium.find_element_by_id("id_remember").is_selected()
        self.selenium.find_element_by_id("id_remember").click()
        self.assertNotEqual(is_checked, self.selenium.find_element_by_id("id_remember").is_selected())
