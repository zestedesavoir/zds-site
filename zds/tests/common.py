from http.client import responses

from django.test import TestCase
from django.test.client import MULTIPART_CONTENT, Client
from tidylib import tidy_document


class ZDSResponseWrapper:
    def __init__(self, response, path):
        self._inner = response
        self.path = path
        if response.headers.get("Content-Type").startswith("text/html"):
            self.html_document, self.errors = tidy_document(
                response.content.decode(),
                options={
                    "doctype": "html5",
                    "drop-empty-elements": 0,
                    "fix-style-tags": "no",
                    # we have proprietary attributes to ensure
                    # compatibility with antidote
                    "warn-proprietary-attributes": 0,
                    "numeric-entities": 1,
                },
            )
            self.valid = not self.errors
        else:
            self.html_document = None
            self.valid = False

    def is_html(self):
        return self.html_document is not None

    def __getattr__(self, attr):
        if not hasattr(self._inner, attr):
            raise AttributeError(f"{self.__class__.__name__} object has no attribute {attr}")
        return getattr(self._inner, attr)


class HTMLValidationMixin:
    failureException = AssertionError

    def assert_valid_if_html(self, response: ZDSResponseWrapper):
        if response.is_html() and not response.valid:
            raise self.failureException(f"{response.path} is not valid HTML: {response.errors}")


class HtmlValidationClient(Client, HTMLValidationMixin):
    def post(
        self,
        path: str,
        data=None,
        content_type=MULTIPART_CONTENT,
        follow=False,
        secure=False,
        *,
        headers=None,
        query_params=None,
        **extra,
    ):
        response = ZDSResponseWrapper(
            super().post(path, data, content_type, follow, secure, headers=headers, query_params=query_params, **extra),
            path,
        )
        self.assert_valid_if_html(response)
        return response

    def get(self, path, data=None, secure=False, *, headers=None, query_params=None, **extra):
        response = ZDSResponseWrapper(
            super().get(path, data, secure, headers=headers, query_params=query_params, **extra), path=path
        )
        self.assert_valid_if_html(response)
        return response

    def put(
        self,
        path,
        data="",
        content_type="application/octet-stream",
        follow=False,
        secure=False,
        *,
        headers=None,
        query_params=None,
        **extra,
    ):
        response = ZDSResponseWrapper(
            super().put(path, data, content_type, follow, secure, headers=headers, query_params=query_params, **extra),
            path,
        )
        self.assert_valid_if_html(response)
        return response


class ZdsTestCase(TestCase):
    client_class = HtmlValidationClient
