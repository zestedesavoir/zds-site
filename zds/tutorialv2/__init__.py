import re

REPLACE_IMAGE_PATTERN = re.compile('(?P<start>)(?P<text>!\[.*?\]\()(?P<url>.+?)(?P<end>\))')
VALID_SLUG = re.compile(r'^[a-z0-9\-_]+$')
