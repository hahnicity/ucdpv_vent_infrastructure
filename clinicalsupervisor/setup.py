#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

from clinicalsupervisor import __version__


setup(name='clinicalsupervisor',
      version=__version__,
      description='Clinical supervisor app for B2C',
      packages=find_packages(exclude=['*.tests']),
      install_requires=[
          'Flask>=0.10',
          'uwsgi',
      ],
      entry_points={
          'console_scripts': [
              'development = clinicalsupervisor.development:main',
          ]
      },
      include_package_data=True,
      )
