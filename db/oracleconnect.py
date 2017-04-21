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
"""
oracleconnect
~~~~~~~~~~~~~

Connection module to oracle db
"""
import argparse
import csv
from datetime import datetime, timedelta
import os
import shutil
from StringIO import StringIO
import sys

import cx_Oracle

DB_TS_DATETIMED_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DB_TS_STATEMENT_FORMAT = "YYYY-MM-DD HH24:MI:SS.FF"
RETRIEVER_DIR = "/Users/retriever/Data"
RESTING_DIR = "/Users/retriever"
VENT_FILE_TS_FORMAT = "%Y-%m-%d-%H-%M-%S.%f"
TS_INCREMENT = timedelta(seconds=0.02)
csv.field_size_limit(sys.maxsize)

# XXX remove host and password


def set_microseconds(ts):
    micro = int(str(ts.microsecond)[:2])
    tail = str(ts.microsecond)[2:]
    if int(tail) > 5 * (10 ** (len(tail) - 1)):
        micro += 1
    ts = ts.replace(microsecond=micro)
    return ts


def gather_vent_files(specific_dir):
    """
    Determine if new pseudo-id'd directories have made it into
    /Users/retriever/Data.
    """
    items = []
    # If a specific directory return all the files from that.
    if specific_dir:
        for root, _, files in os.walk(specific_dir):
            files = map(lambda f: os.path.join(root, f), files)
            items.extend(files)
        return items

    for root, _, files in os.walk(RETRIEVER_DIR):
        last_dir = root.split("/")[-1]
        if "rpi" not in last_dir and root != RETRIEVER_DIR:
            files = map(lambda f: os.path.join(root, f), files)
            items.extend(files)

    return items


def get_file_data(file_path):
    """
    return a dictionary of vent data that looks like

    [
        [<ventbn1>, <datetime1>, <flow1>, <pressure1>],
        [<ventbn1>, <datetime2>, <flow2>, <pressure2>],
        ...
        [<ventbni>, <datetimei>, <flowi>, <pressurei>],
        ...
    ]
    """
    vent_data = []
    with open(file_path) as file_:
        stringio = StringIO()
        stringio.write(file_.read().replace("\x00", ""))
        stringio.seek(0)
        stringio.readline()
        column_line = stringio.readline().rstrip(",\n")
	if not column_line:
	    column_line = stringio.readline().rstrip(",\n")
        columns = len(column_line.split(","))
        stringio.seek(0)
        # If we are using the latest generation of file then set our timestamp to the
        # time we find at the top of the file
        if columns == 2:
            start_datetime = stringio.readline().rstrip("\n")
            cur_ts = datetime.strptime(start_datetime, VENT_FILE_TS_FORMAT)
            cur_ts = set_microseconds(cur_ts)  # ensure microseconds are only 2 decimals
        if columns > 3:  # If somehow we grab an annotation file
            return []
        reader = csv.reader(stringio)
        current_bn = None
        was_be_before = False
        # I need to know what monica does with breaths w/o BS and BE. For now
        # punt
        for row in reader:
            if not row:
                continue
            # XXX Should probably have a better way of failing if we don't find
            # BS or BE properly. The vent bn can probably just be incremented by
            # 1. If BE isn't found then so big deal.
            try:
                row[columns - 2]
            except IndexError:
                continue
            if "BS" in row[columns - 2]:
                try:
                    row[columns - 1]
                except IndexError:
                    continue
                was_be_before = False
                current_bn = int(row[columns - 1].replace("S:", ""))
                continue
            elif "BE" in row[columns - 2] or was_be_before:
                # Do nothing for now. If we had a BE but no BS then just skip the
                # breath.
                was_be_before = True
                continue
            # Ensure file integrity
            try:
                float(row[columns - 1])
                float(row[columns - 2])
            except (IndexError, ValueError):
                continue
            # Ensure data has a BN
            if not current_bn:
                continue
            # Set timestamp in accordance to file version
            if columns == 2:
                cur_ts = cur_ts + TS_INCREMENT
                db_ts_input = cur_ts.strftime(DB_TS_DATETIMED_FORMAT)
            else:
                db_ts_input = row[0]
            # Part where we attach (<datetime>, <flow>, <pressure>)
            vent_data.append([
                current_bn,
                db_ts_input,
                round(float(row[columns - 2]), 2),
                round(float(row[columns - 1]), 2)
            ])
    return vent_data


def move_dirs_to_final_resting_place(filepaths):
    dirs = set()
    for i in filepaths:
        dirs.add(os.path.dirname(i))

    for dir in dirs:
        last = dir.split("/")[-1]
        dest = os.path.join(RESTING_DIR, last)
        shutil.move(dir, dest)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help="Path with vent files to add")
    args = parser.parse_args()
    file_paths = gather_vent_files(args.path)
    if not file_paths:
        print("No vent files found!")
        return

    with cx_Oracle.connect('ri_vent_wvfrm/changeme@ctscdb02.ucdmc.ucdavis.edu/i2b2etl') as con:
        cursor = con.cursor()
        for file_path in file_paths:
            pseudo_id = os.path.dirname(file_path).split("/")[-1]
            vent_data = get_file_data(file_path)
            values = []
            for item in vent_data:
                values.append((item[0], item[1], pseudo_id, item[2], item[3]))
            # executemany is by far the best way to do bulk inserts. What might take 30 minutes
            # is cut down to about 2 minutes.
            cursor.executemany(
                "insert into vent_data (vent_bn, time, pseudo_id, flow, pressure) values "
                "(:1, to_timestamp(:2, '{}'), :3, :4, :5)".format(DB_TS_STATEMENT_FORMAT),
                values
            )
        # Don't commit anything until we're positive the whole transaction should go through
        con.commit()
    move_dirs_to_final_resting_place(file_paths)


if __name__ == "__main__":
    main()
