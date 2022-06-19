import re

REPLACE_IMAGE_PATTERN = re.compile(r"(?P<start>)(?P<text>!\[.*?\]\()(?P<url>.+?)(?P<end>\))")
