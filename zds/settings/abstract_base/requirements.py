from .config import config

# best quality, 100 is the same but documentation says
# ' values up to 100 are allowed, but this is not recommended'
# so let's use 95
THUMBNAIL_QUALITY = 95
# Let's use the default value BUT if we want to let png in lossless format, we have tu use (png,) instead of None
THUMBNAIL_PRESERVE_EXTENSIONS = ("svg",)


social_auth_config = config.get("social_auth", {})

SOCIAL_AUTH_CLEAN_USERNAME_FUNCTION = "zds.member.validators.clean_username_social_auth"

SOCIAL_AUTH_RAISE_EXCEPTIONS = False

SOCIAL_AUTH_FACEBOOK_SCOPE = ["email"]
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {"fields": "name,email"}

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.social_auth.associate_by_email",
    "social_core.pipeline.user.create_user",
    "zds.member.models.save_profile",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

# Before adding new providers such as Facebook and Google,
# you need to make sure they validate the user's email address on sign up!
# If they don't, a malicious person could take control of someone else account!
SOCIAL_AUTH_FACEBOOK_KEY = social_auth_config.get("facebook_key", "")
SOCIAL_AUTH_FACEBOOK_SECRET = social_auth_config.get("facebook_secret", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = social_auth_config.get(
    "google_oauth2_key",
    "696570367703-r6hc7mdd27t1sktdkivpnc5b25i0uip2.apps.googleusercontent.com",
)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = social_auth_config.get(
    "google_oauth2_secret",
    "mApWNh3stCsYHwsGuWdbZWP8",
)

SOCIAL_AUTH_SANITIZE_REDIRECTS = social_auth_config.get(
    "sanitize_redirects",
    False,
)


recaptcha_config = config.get("recaptcha", {})

USE_CAPTCHA = recaptcha_config.get("use_captcha", False)
RECAPTCHA_PUBLIC_KEY = recaptcha_config.get("public_key", "dummy")
RECAPTCHA_PRIVATE_KEY = recaptcha_config.get("private_key", "dummy")


OAUTH2_PROVIDER = {"OAUTH2_BACKEND_CLASS": "oauth2_provider.oauth2_backends.JSONOAuthLibCore"}
