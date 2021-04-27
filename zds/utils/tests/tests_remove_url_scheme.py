import copy

from django.conf import settings
from django.test import TestCase, override_settings

from zds.utils.templatetags.remove_url_scheme import remove_url_scheme


class RemoveUrlSchemeTests(TestCase):
    @staticmethod
    def get_cases(internal_hostname):
        """Return test cases corresponding to different URLs types."""
        return {
            "no scheme, no hostname": {"input": "/bla.html", "expected_output": "/bla.html"},
            "http scheme, internal hostname": {
                "input": f"http://{internal_hostname}/media/gallery/1/1.png",
                "expected_output": "/media/gallery/1/1.png",
            },
            "https scheme, internal hostname": {
                "input": f"https://{internal_hostname}/media/gallery/1/1.png",
                "expected_output": "/media/gallery/1/1.png",
            },
            "no scheme, internal hostname": {
                "input": f"{internal_hostname}/media/gallery/1/1.png",
                "expected_output": "/media/gallery/1/1.png",
            },
            "no scheme, external hostname": {
                "input": "example.com/media/gallery/1/1.png",
                "expected_output": "example.com/media/gallery/1/1.png",
            },
            "http scheme, external hostname, internal hostname in query": {
                "input": f"http://example.com/?q=http://{internal_hostname}",
                "expected_output": f"http://example.com/?q=http://{internal_hostname}",
            },
        }

    def run_cases(self, hostname):
        """Test url_remove_scheme on all URL cases for a given hostname."""
        overridden_zds_app = copy.deepcopy(settings.ZDS_APP)
        overridden_zds_app["site"]["dns"] = hostname
        with override_settings(ZDS_APP=overridden_zds_app):
            internal_hostname = settings.ZDS_APP["site"]["dns"]
            test_cases = RemoveUrlSchemeTests.get_cases(internal_hostname)
            for case_name, case in test_cases.items():
                with self.subTest(msg=case_name):
                    self.assertEqual(case["expected_output"], remove_url_scheme(case["input"]))

    def test_url_remove_scheme(self):
        """Test url_remove_scheme for different hostnames."""
        hostnames = [
            "127.0.0.1:8000",  # Raw IP with port
            "localhost:8000",  # Name with port
            "beta.zestedesavoir.com",  # Name without port, but with subdomain
            "zestedesavoir.com",
        ]  # Name without port again
        for hostname in hostnames:
            with self.subTest(msg=hostname):
                self.run_cases(hostname)
