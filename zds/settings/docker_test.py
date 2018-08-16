from .abstract_base import *
from .docker import *

# Unlike settings_docker_test.py, we don't change the database
# location here.  We don't care if the database file is outside of the
# volume, we don't care about persistence.

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': 'localhost',
        'PORT': '',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    },
}

for logger in LOGGING['loggers'].values():
    logger['level'] = 'ERROR'

ZDS_APP['article']['repo_path'] = join(BASE_DIR, 'articles-data-test')
ZDS_APP['opinions']['repo_path'] = join(BASE_DIR, 'opinions-data-test')

ZDS_APP['tutorial']['repo_path'] = join(BASE_DIR, 'tutoriels-private-test')
ZDS_APP['tutorial']['repo_public_path'] = join(BASE_DIR, 'tutoriels-public-test')

ZDS_APP['content']['repo_private_path'] = join(BASE_DIR, 'contents-private-test')
ZDS_APP['content']['repo_public_path'] = join(BASE_DIR, 'contents-public-test')

