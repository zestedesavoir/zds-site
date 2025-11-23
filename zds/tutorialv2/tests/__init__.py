import copy
import shutil

from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from zds.tutorialv2.models.database import Validation

overridden_zds_app = copy.deepcopy(settings.ZDS_APP)
overridden_zds_app["content"]["repo_private_path"] = settings.BASE_DIR / "contents-private-test"
overridden_zds_app["content"]["repo_public_path"] = settings.BASE_DIR / "contents-public-test"
overridden_zds_app["content"]["extra_content_generation_policy"] = "SYNC"


class override_for_contents(override_settings):
    def __init__(self, **kwargs):
        kwargs.update(MEDIA_ROOT=settings.BASE_DIR / "media-test", ZDS_APP=overridden_zds_app)

        if "SEARCH_ENABLED" not in kwargs:
            kwargs.update(SEARCH_ENABLED=False)

        super().__init__(**kwargs)


class TutorialTestMixin:
    overridden_zds_app = overridden_zds_app

    def clean_media_dir(self):
        shutil.rmtree(self.overridden_zds_app["content"]["repo_private_path"], ignore_errors=True)
        shutil.rmtree(self.overridden_zds_app["content"]["repo_public_path"], ignore_errors=True)
        shutil.rmtree(self.overridden_zds_app["content"]["extra_content_watchdog_dir"], ignore_errors=True)

        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def tearDown(self):
        self.clean_media_dir()
        self.client.logout()


class TutorialFrontMixin:
    def find_element(self, element):
        return self.selenium.find_element(By.CSS_SELECTOR, element)

    def login(self, profile):
        """
        TODO: This is definitely way too slow. Fasten this.
        """
        self.selenium.get(self.live_server_url + reverse("member-login"))

        username = self.find_element(".content-container input#id_username")
        password = self.find_element(".content-container input#id_password")
        username.send_keys(profile.user.username)
        password.send_keys("hostel77")

        self.find_element(".content-container button[type=submit]").click()

        # Wait until the user is logged in (this raises if the element
        # is not found).

        self.find_element(".header-container .logbox #my-account .username")

    def login_author(self):
        self.login(self.user_author.profile)

    def login_staff(self):
        self.login(self.user_staff.profile)

    def logout(self):
        self.find_element("#my-account").click()
        self.find_element('form[action="/membres/deconnexion/"] button').click()

    def ask_validation(self):
        self.selenium.get(self.live_server_url + self.content.get_absolute_url())
        self.find_element('a[href="#ask-validation"]').click()
        self.find_element("#ask-validation textarea").send_keys("Coucou.")
        self.find_element('#ask-validation button[type="submit"]').click()

    def take_reservation(self):
        self.selenium.get(self.live_server_url + self.content.get_absolute_url())
        validation = Validation.objects.filter(content=self.content).first()
        self.find_element(f'form[action="/validations/reserver/{validation.pk}/"] button').click()

    def validate(self):
        self.selenium.get(self.live_server_url + self.content.get_absolute_url())
        validation = Validation.objects.filter(content=self.content).first()
        self.find_element('a[href="#valid-publish"]').click()
        self.find_element("form#valid-publish textarea").send_keys("Coucou.")
        self.find_element(f'form[action="/validations/accepter/{validation.pk}/"] button').click()

    def wait_element_attribute_change(self, locator, attribute, initial_value, time):
        return WebDriverWait(self.selenium, time).until(AttributeHasChanged(locator, attribute, initial_value))


class AttributeHasChanged:
    def __init__(self, locator, attribute_name, initial_value):
        self.locator = locator
        self.attribute_name = attribute_name
        self.initial_value = initial_value

    def __call__(self, driver):
        element = driver.find_element(*self.locator)
        return element.get_attribute(self.attribute_name) != self.initial_value
