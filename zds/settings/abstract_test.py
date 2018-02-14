from .abstract_base.base_dir import BASE_DIR
from .abstract_base.zds import ZDS_APP

DEBUG = False

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
)

MEDIA_ROOT = str(BASE_DIR / 'media-test')

ZDS_APP['content']['repo_private_path'] = str(BASE_DIR / 'contents-private-test')
ZDS_APP['content']['repo_public_path'] = str(BASE_DIR / 'contents-public-test')
ZDS_APP['content']['extra_content_generation_policy'] = 'SYNC'
