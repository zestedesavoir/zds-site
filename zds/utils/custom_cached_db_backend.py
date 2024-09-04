from django.contrib.sessions.backends.cached_db import SessionStore as CachedDBStore
from django.contrib.sessions.base_session import AbstractBaseSession
from django.db import models


class CustomSession(AbstractBaseSession):
    """Custom session model to link each session to its user.
    This is necessary to list a user's sessions without having to browse all sessions.
    Based on https://docs.djangoproject.com/en/4.2/topics/http/sessions/#example

    This will create a table named utils_customsession and use it instead of
    the table django_session. The content of the latest can be dropped."""

    account_id = models.IntegerField(null=True, db_index=True)

    @classmethod
    def get_session_store_class(cls):
        return SessionStore


class SessionStore(CachedDBStore):
    """Custom session store for the custom session model."""

    cache_key_prefix = "zds.utils.custom_cached_db_backend"

    @classmethod
    def get_model_class(cls):
        return CustomSession

    def create_model_instance(self, data):
        obj = super().create_model_instance(data)
        try:
            account_id = int(data.get("_auth_user_id"))
        except (ValueError, TypeError):
            account_id = None
        obj.account_id = account_id
        return obj
