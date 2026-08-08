import os
from pathlib import Path

# tomllib was added to the standard library in Python 3.11
# tomli is only needed for older Python versions
# both libraries are strictly identical, only the name differs
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


config = {}

if config_path := os.environ.get("ZDS_CONFIG"):
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    print(f"Using the config file at {config_path!r}")

django_setting = os.environ.get("DJANGO_SETTINGS_MODULE")

key = "ensure_settings_module"

if key in config and config[key] != django_setting:
    raise Exception(
        (
            "The DJANGO_SETTINGS_MODULE environment variable is different than "
            "the `ensure_settings_module` setting in {!r}. "
            "You are probably doing something wrong."
        ).format(config_path)
    )
