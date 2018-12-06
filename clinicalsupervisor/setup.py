"""
ucdv_vent_infrastructure "Platform for collecting, aggregating, and storing ventilator data"
Copyright (C) 2017 Gregory Rehm

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
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
          'mysql-python',
          'pandas',
          'sqlalchemy',
          'uwsgi',
      ],
      entry_points={
          'console_scripts': [
              'development = clinicalsupervisor.development:main',
          ]
      },
      include_package_data=True,
      )
