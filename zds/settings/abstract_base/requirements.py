from .config import config

# best quality, 100 is the same but documentation says
# ' values up to 100 are allowed, but this is not recommended'
# so let's use 95
THUMBNAIL_QUALITY = 95
# Let's use the default value BUT if we want to let png in lossless format, we have tu use (png,) instead of None
THUMBNAIL_PRESERVE_EXTENSIONS = None


social_auth_config = config.get('social_auth', {})

SOCIAL_AUTH_RAISE_EXCEPTIONS = False

SOCIAL_AUTH_GOOGLE_OAUTH2_USE_DEPRECATED_API = True
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',
    'social.pipeline.user.get_username',
    'social.pipeline.user.create_user',
    'zds.member.models.save_profile',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details'
)

SOCIAL_AUTH_FACEBOOK_KEY = social_auth_config.get('facebook_key', '')
SOCIAL_AUTH_FACEBOOK_SECRET = social_auth_config.get('facebook_secret', '')

SOCIAL_AUTH_TWITTER_KEY = social_auth_config.get('twitter_key', '')
SOCIAL_AUTH_TWITTER_SECRET = social_auth_config.get('twitter_secret', '')

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = social_auth_config.get(
    'google_oauth2_key',
    '696570367703-r6hc7mdd27t1sktdkivpnc5b25i0uip2.apps.googleusercontent.com',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = social_auth_config.get(
    'google_oauth2_secret',
    'mApWNh3stCsYHwsGuWdbZWP8',
)

SOCIAL_AUTH_SANITIZE_REDIRECTS = social_auth_config.get(
    'sanitize_redirects',
    False,
)


recaptcha_config = config.get('recaptcha', {})

USE_CAPTCHA = recaptcha_config.get('use_captcha', False)
# Seems to be used by `django-recaptcha` (what a poorly-namespaced
# setting!).
# Set to `True` to use the “No Captcha” engine instead of the old API.
NOCAPTCHA = True
RECAPTCHA_USE_SSL = True
RECAPTCHA_PUBLIC_KEY = recaptcha_config.get('public_key', 'dummy')
RECAPTCHA_PRIVATE_KEY = recaptcha_config.get('private_key', 'dummy')


OAUTH2_PROVIDER = {
    'OAUTH2_BACKEND_CLASS': 'oauth2_provider.oauth2_backends.JSONOAuthLibCore'
}
