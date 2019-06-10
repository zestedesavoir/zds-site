import os
from pathlib import Path
import toml


default_config_path = str(Path.cwd() / 'config.toml')
config_path = os.environ.get('ZDS_CONFIG', default_config_path)

try:
    config = toml.load(config_path)
    print('Using the config file at {!r}'.format(config_path))
except OSError:
    config = {}

django_setting = os.environ.get('DJANGO_SETTINGS_MODULE')

key = 'ensure_settings_module'

if key in config and config[key] != django_setting:

    raise Exception((
        'The DJANGO_SETTINGS_MODULE environment variable is different than '
        'the `ensure_settings_module` setting in {!r}. '
        'You are probably doing something wrong.'
    ).format(config_path))
