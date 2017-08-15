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
import pandas as pd


def raw_vwd_to_db(db, chunksize, vwd_gen, pseudo_id):
    flow = []
    pressure = []
    patient = []
    abs_bs = []
    vent_bn = []
    for breath in vwd_gen:
        if len(breath['ts']) == 0:
            raise Exception('There is no absolute bs time!')
        abs = breath['ts'][0]
        flow.extend(breath['flow'])
        pressure.extend(breath['pressure'])
        patient.extend([pseudo_id] * len(breath['flow']))
        abs_bs.extend([abs] * len(breath['flow']))
        vent_bn.extend([breath['vent_bn']] * len(breath['flow']))
    df = pd.DataFrame([flow, pressure, patient, abs_bs, vent_bn]).transpose()
    df.columns = ['flow', 'pressure', 'patient', 'abs_bs', 'vent_bn']
    df.to_sql("vwd", db, index=False, chunksize=chunksize, if_exists="append")
