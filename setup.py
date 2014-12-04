#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# https://docs.djangoproject.com/en/dev/intro/reusable-apps/

import os

from pip.req import parse_requirements

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='zds',
    version='1.3',
    packages=['zds'],
    include_package_data=True,
    license='GPLv3',
    description='Site internet communautaire codé à l\'aide du framework Django 1.6 et de Python 2.7.',
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
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[str(pkg.req) for pkg in parse_requirements('requirements.txt')],
    tests_require=[str(pkg.req) for pkg in parse_requirements('requirements-dev.txt')],
)