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
from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.types import DateTime, Float, Integer


metadata = MetaData()

vwd = Table('vwd', metadata,
    Column('id', Integer, autoincrement=True, primary_key=True),
    Column('flow', Float(precision=2)),
    Column('pressure', Float(precision=2)),
    Column('patient', String(20), index=True),
    Column('abs_bs', DateTime, index=True),
    Column('vent_bn', Integer)
)
