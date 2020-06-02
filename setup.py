#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
setup.py
A module that installs agrcgeocoding as a module
"""
import io
import json
from glob import glob
from os.path import basename, dirname, join, splitext

from setuptools import find_packages, setup


def read(*names, **kwargs):
    """read the contents of a file
    """
    with io.open(join(dirname(__file__), *names), encoding=kwargs.get('encoding', 'utf8')) as file_handler:
        return file_handler.read()


setup(
    name='agrcgeocoding',
    version=json.loads(read('tool-version.json'))['PRO_VERSION_NUMBER'],
    license='MIT',
    description='Geocoding with the AGRC Web API.',
    author='AGRC',
    author_email='agrc@utah.gov',
    url='https://github.com/agrc/geocoding-toolbox',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
    ],
    project_urls={
        'Issue Tracker': 'https://github.com/agrc/geocoding-toolbox/issues',
    },
    keywords=['geocoding', 'gis'],
    install_requires=['requests==2.23.*'],
    extras_require={
        'dev': [
            'docopt==0.6.*',
            'gitpython==3.1.*',
            'pylint-quotes==0.2.*',
            'pylint==2.5.*',
            'pytest-cov==2.9.*',
            'pytest-instafail==0.4.*',
            'pytest-isort==1.0.*',
            'pytest-pylint==0.17.*',
            'pytest-watch==4.2.*',
            'pytest==5.4.*',
            'requests-mock==1.8.*',
            'yapf==0.30.*',
        ]
    },
    setup_requires=[
        'pytest-runner',
    ],
    entry_points={'console_scripts': [
        'agrcgeocoding = agrcgeocoding.geocode:main',
    ]},
)
