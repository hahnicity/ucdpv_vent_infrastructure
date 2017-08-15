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


Doc: Extract raw data from a file and return it in some kind of presentable format
"""
import csv
from datetime import datetime, timedelta
import io
import re
from operator import xor
from StringIO import StringIO
import sys


csv.field_size_limit(sys.maxsize)
EMPTY_FLOAT_DELIMITER = -1000.0
EMPTY_DATE_DELIMITER = "2222-12-12 12:12:12.12"

def clear_descriptor_null_bytes(descriptor):
    descriptor_text = descriptor.read()
    stringio = StringIO()
    stringio.write(descriptor_text.replace("\x00", ""))
    stringio.seek(0)
    return stringio


def detect_csv_version(first):
    """
    Detect timestamp, number columns, and whether there is a timestamp on
    first row and/or timestamp on first col
    """
    first = first.strip(',\r\n')
    if len(first.split(','))==3 or len(first.split('-'))==3:
        timestamp_1st_col = True
        timestamp_1st_row = False
        bs_col = 1
        ncol = 3

    #detect 3rd type, with date time in first row
    elif len(first.split('-'))==6:
        timestamp_1st_col = False
        timestamp_1st_row = True
        bs_col = 0
        ncol = 2

    #detect 1st type, 2 col  #BS, S:52335,\n (by default)
    else:
        timestamp_1st_col = False
        timestamp_1st_row = False
        bs_col = 0
        ncol = 2
    return  bs_col, ncol, timestamp_1st_col, timestamp_1st_row


def filter_arrays(flow, pressure, t_array, timestamp_array):
    # Array filtering speedup
    if flow[0] == EMPTY_FLOAT_DELIMITER:
        return [], [], [], []
    for idx, i in enumerate(flow):
        if i == EMPTY_FLOAT_DELIMITER:
            final_rel_idx = idx
            break
    if timestamp_array[0] == EMPTY_DATE_DELIMITER:
        final_ts_idx = 0
    else:
        final_ts_idx = final_rel_idx
    # Don't add  + 1 because we are tracking up to the empty delim
    flow = flow[:final_rel_idx]
    pressure = pressure[:final_rel_idx]
    t_array = t_array[:final_rel_idx]
    timestamp_array = timestamp_array[:final_ts_idx]
    return flow, pressure, t_array, timestamp_array


def reset_arrays(flow, pressure, t_array, timestamp_array):
    n_obs = 2000
    flow = [EMPTY_FLOAT_DELIMITER] * n_obs
    pressure = [EMPTY_FLOAT_DELIMITER] * n_obs
    t_array = [EMPTY_FLOAT_DELIMITER] * n_obs
    timestamp_array = [EMPTY_DATE_DELIMITER] * n_obs
    return flow, pressure, t_array, timestamp_array


def extract_raw(descriptor,
                ignore_missing_bes,
                rel_bn_interval=[],
                vent_bn_interval=[],
                spec_rel_bns=[],
                spec_vent_bns=[]):
    """
    Takes a file descriptor and returns the raw data on the
    breath for us to use. Returns data in format

    {
        'vent_bn': vent_bn,
        't': [rel_t1, rel_t2, ...],
        'ts': [ts1, ts2, ...],
        'flow': [flow1, flow2, ...],
        'pressure': [pressure1, pressure2, ...],
        'be_count': be_count,
        'bs_count': bs_count,
        ....
    }

    :param descriptor: The file descriptor to use
    :param ignore_missing_bes: boolean whether or not to ignore missing BEs in the data (False if we want to use breaths without a BE, True otherwise)
    :param rel_bn_interval: The relative [start, end] interval for the data
    :param vent_bn_interval: The vent bn [start, end] interval for the data
    :param spec_rel_bns: The specific relative bns that we want eg: [1, 10, 20]
    :param spec_vent_bns: The specific vent bns that we want eg: [1, 10, 20]
    """
    def get_data(flow, pressure, t_array, ts_array, rel_bn, vent_bn, bs_count, be_count, last_t, t_delta):
        flow, pressure, t_array, ts_array = filter_arrays(
            flow, pressure, t_array, ts_array
        )
        if flow:
            data_dict = {
                "rel_bn": rel_bn,
                "vent_bn": vent_bn,
                "flow": flow,
                "pressure": pressure,
                "t": t_array,
                "ts": ts_array,
                "bs_count": bs_count,
                "be_count": be_count,
                "bs_time": bs_time,
                "frame_dur": t_array[-1] + t_delta,
                "dt": t_delta,
            }
            return data_dict

    if not isinstance(descriptor, file) and not isinstance(descriptor, StringIO) and not "cStringIO" in str(descriptor.__class__) and not isinstance(descriptor, io.TextIOWrapper):
        raise ValueError("Provide a file descriptor as input!")
    if (len(rel_bn_interval) == 0 and len(vent_bn_interval) == 0 and
        len(spec_rel_bns) == 0 and len(spec_vent_bns) == 0):
        pass
    elif not xor(
            xor(len(rel_bn_interval) > 0, len(vent_bn_interval) > 0),
            xor(len(spec_rel_bns) > 0, len(spec_vent_bns) > 0)
        ):
        raise ValueError("You can only specify one vent or rel bn filtering option for use!")
    spec_rel_bns = sorted(spec_rel_bns)
    spec_vent_bns = sorted(spec_vent_bns)
    collection_start = False
    last_t = 0  # first data point starts at 0
    bs_count = 0
    be_count = 0
    bs_time = 0.02
    t_delta = 0.02
    rel_ts = 0
    vent_bn = 0
    rel_bn = 0
    has_bs = False
    idx = 0
    flow, pressure, t_array, timestamp_array = reset_arrays(None, None, None, None)
    descriptor = clear_descriptor_null_bytes(descriptor)
    reader = csv.reader(descriptor)
    data_dict = {}
    vent_bn_regex = re.compile("S:(\d+)")
    descriptor.seek(0)
    first_line = descriptor.readline()
    bs_col, ncol, ts_1st_col, ts_1st_row = detect_csv_version(first_line)
    if ts_1st_row:
        abs_time = datetime.strptime(first_line.strip('\r\n'), "%Y-%m-%d-%H-%M-%S.%f")
    descriptor.seek(0)

    for row in reader:
        try:
            row[bs_col]
        except IndexError:
            continue
        if row[bs_col].strip() == "BS":
            collection_start = True
            if not ignore_missing_bes and has_bs:
                data = get_data(
                    flow, pressure, t_array, timestamp_array, rel_bn, vent_bn, bs_count, be_count, bs_time, t_delta
                )
                if data:
                    yield data
                bs_time = round(last_t + 0.02, 2)
            rel_ts = 0
            bs_count += 1
            rel_bn += 1
            idx = 0
            has_bs = True
            flow, pressure, t_array, timestamp_array = reset_arrays(
                flow, pressure, t_array, timestamp_array
            )
            try:
                match = vent_bn_regex.search(row[bs_col + 1])
            except IndexError:
                has_bs = False
                continue
            if not match:
                has_bs = False  # Don't collect data for the breath
                continue
            vent_bn = int(match.groups()[0])
            if rel_bn_interval and rel_bn > rel_bn_interval[1]:
                raise StopIteration
            elif vent_bn_interval and vent_bn > vent_bn_interval[1]:
                raise StopIteration
            elif spec_rel_bns and rel_bn > spec_rel_bns[-1]:
                raise StopIteration
            elif spec_vent_bns and vent_bn > spec_vent_bns[-1]:
                raise StopIteration
            elif vent_bn_interval and not (vent_bn_interval[0] <= vent_bn <= vent_bn_interval[1]):
                has_bs = False
            elif rel_bn_interval and not (rel_bn_interval[0] <= rel_bn <= rel_bn_interval[1]):
                has_bs = False
            elif spec_rel_bns and (rel_bn not in spec_rel_bns):
                has_bs = False
            elif spec_vent_bns and (vent_bn not in spec_vent_bns):
                has_bs = False
        elif row[bs_col].strip() == "BE":
            be_count += 1
            has_bs = False
            data = get_data(
                flow, pressure, t_array, timestamp_array, rel_bn, vent_bn, bs_count, be_count, bs_time, t_delta
            )
            if data:
                yield data
            bs_time = round(last_t + 0.02, 2)
            rel_ts = 0
        else:
            if collection_start:  # if there is stray data at the top of the file
                last_t = round(last_t + .02, 2)

            if not has_bs:
                continue
            try:
                flow[idx] = round(float(row[ncol - 2]), 2)
                pressure[idx] = round(float(row[ncol - 1]), 2)
            except (IndexError, ValueError):
                continue
            t_array[idx] = round(rel_ts, 2)
            if ts_1st_col:
                timestamp_array[idx] = row[0]
            elif ts_1st_row:
                timestamp_array[idx] = (abs_time + timedelta(seconds=last_t)).strftime("%Y-%m-%d %H-%M-%S.%f")
            rel_ts = round(rel_ts + t_delta, 2)
            idx += 1
