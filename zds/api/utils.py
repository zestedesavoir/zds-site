from oauth2_provider.models import Application, AccessToken

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
        "/oauth2/token/",
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
