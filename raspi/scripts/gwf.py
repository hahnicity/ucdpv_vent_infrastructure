"""
ucdv_vent_infrastructure "Platform for collecting, aggregating, and storing ventilator
 data"
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
gwf.py
~~~~~~

New gwf script. All the old shell script should do is essentially call this one.
Pythonizing this script allows us to perform testing on the functions and mocking
on components we need to mock.
"""
from itertools import cycle
import logging
import re
import subprocess
import traceback
import time

import get_serial

CannedPopen = lambda args: subprocess.Popen(
    args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
RANDOM_DELAY_PARAM = 300
SYNC_TIMEOUT = 5
ENV_TYPE = "prod"
GET_SERIAL_FAILURE_WAIT = 60
NETWORKING_RESTART_WAIT = 10


def get_process(args):
    logging.debug("Perform command: {}".format(" ".join(args)))
    return CannedPopen(args)


def perform_command_and_validate(process, err_msg):
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        logging.error("Err: '{}' killing gwf!\n\nReason: {}".format(err_msg, stderr))
        raise Exception("{}\n\n{}".format(err_msg, stderr))
    return stdout, stderr


def check_if_wifi_available():
    # XXX Is this the best way to determine if wifi will work??
    process = get_process(["ip", "a", "show", "wlan0"])
    stdout, stderr = perform_command_and_validate(process, "unable to show wifi status!")
    wifi_state_regex = r"state[\t ]*(UP|DOWN)"
    mapping = {"UP": True, "DOWN": False}
    split_out = filter(lambda x: x.strip(), stdout.split("\n"))
    try:
        state = re.search(wifi_state_regex, split_out[0]).groups()[0]
    except AttributeError:
        return False
    else:
        return mapping[state]


def check_if_synced():
    process = get_process(["ntpq", "-nc", "peers"])
    stdout, stderr = perform_command_and_validate(process, "unable to get ntp peers")
    list_peers = stdout.split("\n")
    ip_pattern = "^[\+\*](?P<ip>\d+.\d+.\d+.\d+)"
    delay = 0
    for line in list_peers:
        match = re.search(ip_pattern, line)
        if match:
            delay_pattern = "[ublsABM] *\d[hd]? *\d+ *\d+ *(?P<delay>\d+\.\d+)"
            match = re.search(delay_pattern, line)
            if not match:
                logging.warn("Encountered weird delay match line: {}".format(line))
                continue
            delay = match.groupdict()["delay"]
            break
    else:
        return False

    # Was this an artifact of translation from when I was writing this script?
    # because I don't see how the delay will be so immense that we should not
    # collect
    if float(delay) < RANDOM_DELAY_PARAM:
        return True
    else:
        return False


def perform_ntp_sync():
    # cycle wireless down/up until we have a connection
    while True:
        if check_if_wifi_available():
            break
        else:
            process = get_process(["sudo", "service", "networking", "restart"])
            perform_command_and_validate(process, "networking service restart failed")
            time.sleep(NETWORKING_RESTART_WAIT)

    logging.info("Starting ntp sync process. Cycling ntp off/on")
    process = get_process(["sudo", "service", "ntp", "stop"])
    perform_command_and_validate(process, "unable to stop ntp")
    # What is the point of this? Why not just restart?
    process = get_process(["sudo", "ntpd", "-gq"])
    process.communicate()
    process = get_process(["sudo", "service", "ntp", "start"])
    perform_command_and_validate(process, "Could not restart ntp")

    while True:
        if check_if_synced():
            return
        else:
            logging.info("Time is not synced. Retrying every {}s".format(SYNC_TIMEOUT))
            time.sleep(SYNC_TIMEOUT)


def execute_get_serial(env_type):
    mapping = {"testing": (lambda : (yield 1))(), "prod": cycle([True])}
    continuation_func = mapping[env_type]
    while continuation_func.next():
        try:
            get_serial.get_serial(env_type)
        except Exception as err:
            logging.warn("Error in get_serial: {}".format(traceback.format_exc()))
            time.sleep(GET_SERIAL_FAILURE_WAIT)


def main():
    logging.basicConfig(
        filename="/var/log/gwf.log",
        format="%(levelname)s:%(asctime)s:%(message)s",
        level=logging.DEBUG
    )
    logging.info("Starting gwf")
    try:
        perform_ntp_sync()
        logging.info("Time is synced. Starting get_serial script")
        execute_get_serial(ENV_TYPE)
    except:
        logging.error(traceback.format_exc())



if __name__ == "__main__":
    main()
