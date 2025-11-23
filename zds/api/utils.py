from django.urls import reverse
from oauth2_provider.models import AccessToken, Application

# As of django-oauth-toolkit (oauth2_provider) 2.0.0, `Application.client_secret` values are hashed
# before being saved in the database. For the tests, we use the same method as django-oauth-toolkit's tests
# which is to store the client_secret cleartext value in CLEARTEXT_SECRET.
# (See https://github.com/jazzband/django-oauth-toolkit/blob/fda64f97974aac78d4ac9c9f0f36e137dbe4fb8c/tests/test_client_credential.py#L26C58-L26C58)
CLEARTEXT_SECRET = "abcdefghijklmnopqrstuvwxyz1234567890"


def authenticate_oauth2_client(client, user, password):
    oauth2_client = Application.objects.create(
        user=user,
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_PASSWORD,
        client_secret=CLEARTEXT_SECRET,
    )
    oauth2_client.save()

    client.post(
        reverse("oauth2_provider:token"),
        {
            "client_id": oauth2_client.client_id,
            "client_secret": CLEARTEXT_SECRET,
            "username": user.username,
            "password": password,
            "grant_type": "password",
        },
    )
    access_token = AccessToken.objects.get(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
