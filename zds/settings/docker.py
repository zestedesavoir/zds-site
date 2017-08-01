from os.path import join

from .abstract_base import *

DB_DIR = join(BASE_DIR, 'db')

# We can't use a Docker volume on a single file. We have to move the
# database to a separate directory.
DATABASES['default']['NAME'] = join(DB_DIR, 'base.db')
MEDIA_ROOT = join(DB_DIR, 'media')
STATIC_ROOT = join(DB_DIR, 'static')
STATICFILES_DIRS = (
    join(BASE_DIR, 'dist'),
)

ZDS_APP['article']['repo_path'] = join(DB_DIR, 'articles-data')

ZDS_APP['opinions']['repo_path'] = join(DB_DIR, 'opinions-data')

ZDS_APP['tutorial']['repo_path'] = join(DB_DIR, 'tutoriels-private')
ZDS_APP['tutorial']['repo_public_path'] = join(DB_DIR, 'tutoriels-public')

ZDS_APP['content']['repo_private_path'] = join(DB_DIR, 'contents-private')
ZDS_APP['content']['repo_public_path'] = join(DB_DIR, 'contents-public')
# I have no idea wtf is this
ZDS_APP['content']['extra_content_watchdog_dir'] = join(
    DB_DIR, 'watchdog-build')
