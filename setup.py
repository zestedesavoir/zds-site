#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# https://docs.djangoproject.com/en/dev/intro/reusable-apps/

import os

from pip.download import PipSession
from pip.req import parse_requirements

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

session = PipSession()
pkgs = ['django-debug-toolbar', 'sqlparse']
for pkg in parse_requirements('requirements.txt', session=session):
    if pkg.req:
        pkgs.append(str(pkg.req))

setup(
    name='zds',
    version='1.7',
    packages=['zds'],
    include_package_data=True,
    license='GPLv3',
    description='Community Website implemented with Django framework and Python 2.',
    long_description=README,
    url='https://github.com/zestedesavoir/zds-site',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 2',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=pkgs,
    tests_require=[str(pkg.req) for pkg in parse_requirements('requirements-dev.txt', session=session)],
)
