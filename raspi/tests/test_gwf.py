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
test_gwf.py
~~~~~~~~~~~

Tests to ensure that gwf works so we avoid all issues we've ran into
in the past.
"""
import datetime

from mock import Mock, patch
from nose.tools import assert_raises, eq_

from raspi.scripts import gwf


class MockProcess(object):
    def __init__(self, stdout, stderr, rc):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = rc

    def communicate(self):
        return self.stdout, self.stderr


def test_perform_command_and_validate_on_success():
    stdout = "foo"
    stderr = ""
    proc = MockProcess(stdout, stderr, 0)
    out, err = gwf.perform_command_and_validate(proc, "Shouldn't happen")
    eq_(out, stdout)
    eq_(err, stderr)


def test_perform_command_and_validate_on_error():
    stdout = "foo"
    stderr = "bar"
    proc = MockProcess(stdout, stderr, 1)
    assert_raises(Exception, gwf.perform_command_and_validate, proc, "blah")


def test_main_integration_get_serial():
    """
    Integration testing for gwf with get_serial
    """
    with patch("raspi.scripts.gwf.perform_ntp_sync") as sync:
        with patch("raspi.scripts.gwf.logging") as logging:
            with patch("raspi.scripts.gwf.get_serial") as get_serial:
                try:
                    gwf.execute_get_serial("testing")
                except StopIteration:
                    pass
                get_serial.get_serial.assert_called_once_with("testing")


def test_error_case_in_ntp_sync():
    with patch("raspi.scripts.gwf.perform_ntp_sync") as sync:
        with patch("raspi.scripts.gwf.logging") as logging:
            with patch("raspi.scripts.gwf.GET_SERIAL_FAILURE_WAIT") as wait:
                wait = .01
                sync.side_effect = ValueError("foobar!")
                try:
                    gwf.execute_get_serial("testing")
                except StopIteration:
                    pass
                expected = "ValueError: foobar!"
                assert expected in logging.warn.call_args_list[0][0][0]


def test_check_if_synced_pos_offset():
    with patch("raspi.scripts.gwf.perform_command_and_validate") as perf:
        response = """
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
+152.79.105.129  129.6.15.30      2 u    2   64    1    1.299    0.167   1.903
*152.79.105.132  173.71.69.90     2 u    1   64    1    1.310   -1.878   1.633
        """
        perf.return_value = (response, "")
        is_synced = gwf.check_if_synced()
        assert is_synced


def test_check_if_synced_weird_match_line():
    with patch("raspi.scripts.gwf.perform_command_and_validate") as perf:
        response = """
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
+152.79.105.129  129.6.15.30
*152.79.105.132  173.71.69.90
        """
        perf.return_value = (response, "")
        is_synced = gwf.check_if_synced()
        assert not is_synced


def test_check_if_synced_neg_offset():
    with patch("raspi.scripts.gwf.perform_command_and_validate") as perf:
        response = """
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
*152.79.105.129  129.6.15.30      2 u    2   64    1    2.480   -0.579   0.001
 152.79.105.132  173.71.69.90     2 u    1   64    1    1.294   -2.128   0.001
        """
        perf.return_value = (response, "")
        is_synced = gwf.check_if_synced()
        assert is_synced


def test_check_if_wifi_available_up_state():
    with patch("raspi.scripts.gwf.perform_command_and_validate") as perf:
        with patch("raspi.scripts.gwf.get_process"):
            response = """
    3: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
        link/ether 00:0f:60:08:07:7c brd ff:ff:ff:ff:ff:ff
        inet 10.190.16.81/20 brd 10.190.31.255 scope global wlan0
           valid_lft forever preferred_lft forever
        inet6 fe80::20f:60ff:fe08:77c/64 scope link
           valid_lft forever preferred_lft forever
            """
            perf.return_value = (response, "")
            is_up = gwf.check_if_wifi_available()
            assert is_up


def test_check_if_wifi_available_down_error_state():
    with patch("raspi.scripts.gwf.perform_command_and_validate") as perf:
        with patch("raspi.scripts.gwf.get_process"):
            response = """
    3: wlan0: <BROADCAST,MULTICAST> mtu qdisc state group qlen
        link/ether 00:0f:60:08:07:7c brd ff:ff:ff:ff:ff:ff
            """
            perf.return_value = (response, "")
            is_up = gwf.check_if_wifi_available()
            assert not is_up

def test_check_if_wifi_available_down_state():
    with patch("raspi.scripts.gwf.perform_command_and_validate") as perf:
        with patch("raspi.scripts.gwf.get_process"):
            response = """
    3: wlan0: <BROADCAST,MULTICAST> mtu 1500 qdisc mq state DOWN group default qlen 1000
        link/ether 00:0f:60:08:07:7c brd ff:ff:ff:ff:ff:ff
            """
            perf.return_value = (response, "")
            is_up = gwf.check_if_wifi_available()
            assert not is_up
