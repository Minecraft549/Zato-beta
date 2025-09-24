# -*- coding: utf-8 -*-

"""
Copyright (C) 2025, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
import os

# flake8: noqa
from setuptools import setup, find_packages

version = '4.1'

def parse_requirements(requirements): # type: ignore
    ignored = ['#', 'setuptools', '-e']

    with open(requirements) as f:
        return [line.split('==')[0] for line in f if line.strip() and not any(line.startswith(prefix) for prefix in ignored)]

_ = setup(
      name = 'zato-common',
      version = version,

      author = 'Zato Source s.r.o.',
      author_email = 'info@zato.io',
      url = 'https://zato.io',
      license = 'AGPLv3',
      platforms = 'OS Independent',
      description = 'Constants and utils common across the whole of Zato ESB and app server (https://zato.io)',

      package_dir = {'':'src'},
      packages = find_packages('src'),
      namespace_packages = ['zato'],

      install_requires = parse_requirements(
          os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements.txt')),

      classifiers = [
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Framework :: Buildout',
          'Intended Audience :: Customer Service',
          'Intended Audience :: Developers',
          'Intended Audience :: Financial and Insurance Industry',
          'Intended Audience :: Healthcare Industry',
          'Intended Audience :: Information Technology',
          'Intended Audience :: Telecommunications Industry',
          'License :: OSI Approved :: AGPLv3',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: C',
          'Programming Language :: Python :: 2 :: Only',
          'Programming Language :: Python :: 2.7',
          'Topic :: Database',
          'Operating System :: POSIX :: Linux',
          'Operating System :: MacOS :: MacOS X',
          'Topic :: Internet',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
          'Topic :: Internet :: File Transfer Protocol (FTP)',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Software Development :: Object Brokering',
          ],

      zip_safe = False,
)
