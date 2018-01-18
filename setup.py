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
    'python-magic>=0.4,<0.5',
    'python-redmine>=2.0,<2.1',
    'six>=1.11',
    'tabulate>=0.8',
    'xlrd>=1.1,<1.2',
]

setup_requirements = [
    # TODO(wandering-tales):
    # put setup requirements(distutils extensions, etc.) here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='redmine_xls_export2jira',
    version='0.1.1',
    description='Convert and merge XLS exports of the "Redmine XLS Export" '
                'plugin to files compatible with the '
                'JIRA Importers plugin (JIM).',
    long_description=readme + '\n\n' + history,
    author="Michele Cardone",
    author_email='michele.cardone82@gmail.com',
    url='https://github.com/wandering-tales/redmine-xls-export2jira',
    packages=find_packages(include=['redmine_xls_export2jira']),
    entry_points={
        'console_scripts': [
            'redmine_xls_export2jira=redmine_xls_export2jira.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='redmine_xls_export2jira',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
