#!/usr/bin/env python
import argparse
import yaml
import zds
import os
from zds import settings

parser = argparse.ArgumentParser(description='Give yaml fixture files.')

parser.add_argument('files', type=str, nargs='+', help="The fixture file name.")

args = parser.parse_args()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zds.settings")

for filename in args.files:
    stream = open(filename, 'r')
    fixture_list = yaml.load(stream)
    for fixture in fixture_list:
        splitted = str(fixture["factory"]).split(".")
        module_part = ".".join(splitted[:-1])
        m = __import__(module_part)
        for comp in splitted[1:-1]:
            m = getattr(m, comp)

        obj = getattr(m, splitted[-1])(**fixture["fields"])
        print(obj)