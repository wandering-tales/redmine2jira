#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'click-default-group>=1.2',
    'contextlib2==0.5.5',
    'future>=0.16.0',
    'inflection>=0.3',
    'isodate>=0.6',
    'lxml>=4.1',
    'markdown>=2.6',
    'Pillow>=5.0',
    'python-redmine==2.2.1',
    'regex>=2018.2',
    'six>=1.11',
    'tabulate>=0.8',
    'textile>=3.0',
]

setup_requirements = [
    # TODO(wandering-tales):
    # put setup requirements(distutils extensions, etc.) here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='redmine2jira',
    version='0.10.3',
    description='Export Redmine issues to file formats compatible '
                'with the JIRA Importers plugin (JIM) ',
    long_description=readme + '\n\n' + history,
    author="Michele Cardone",
    author_email='michele.cardone82@gmail.com',
    url='https://github.com/wandering-tales/redmine2jira',
    packages=find_packages(include=['redmine2jira', 'redmine2jira.*']),
    entry_points={
        'console_scripts': [
            'redmine2jira=redmine2jira.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='redmine2jira',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
