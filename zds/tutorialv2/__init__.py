import re

REPLACE_IMAGE_PATTERN = re.compile(u'(?P<start>)(?P<text>!\[.*?\]\()(?P<url>.+?)(?P<end>\))')
