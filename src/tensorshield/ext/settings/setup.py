#!/usr/bin/env python3
import json
import os
import pathlib
from setuptools import find_namespace_packages
from setuptools import setup


SETUPDIR = pathlib.Path(__file__).parent

packages = find_namespace_packages(
    where=SETUPDIR,
    exclude={'build', 'dist', 'tests', 'var'}
)
opts = json.loads((open(SETUPDIR.joinpath(packages[0], 'package.json')).read()))
version = str.strip(open(SETUPDIR.joinpath('VERSION')).read())
if os.path.exists(SETUPDIR.joinpath('README.md')):
    with open(SETUPDIR.joinpath('README.md'), encoding='utf-8') as f:
        opts['long_description'] = f.read()
        opts['long_description_content_type'] = "text/markdown"

setup(
    version=version,
    packages=packages,
    include_package_data=True,
    **opts)
