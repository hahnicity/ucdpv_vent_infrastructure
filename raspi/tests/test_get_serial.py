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
from copy import copy
from tempfile import NamedTemporaryFile

from mock import MagicMock, patch
from nose.tools import assert_dict_equal, eq_

from scripts.get_serial import get_configuration, get_serial

MOCK_CONFIG = {
    "baudrate": 38400,
    "tty_file": "foo/bar",
    "data_path": "pi/mock/data",
    "refresh_rate": 0.01,
    "vent_disconnect_tolerance": 0.01,
}
MOCK_CONFIG_FILE = """
[config]
baudrate=38400
tty_file=foo/bar
data_path=pi/mock/data
refresh_rate=1000
vent_disconnect_tolerance=1
"""
MOCK_SERIAL_RESPONSE = "line"
vent_disc_iterator = iter([1, 1] + [0] * 10000)


def test_get_configuration_from_main():
    with patch("scripts.get_serial.open") as mock_open:
        with patch("scripts.get_serial.serial") as mock_serial:
            with patch("scripts.get_serial.retrieve_data") as mock_retriever:
                with NamedTemporaryFile() as tmp:
                    with open(tmp.name, "r+w") as mock_config_file:
                        mock_config_file.write(MOCK_CONFIG_FILE)
                        mock_config_file.flush()
                        mock_config_file.seek(0)
                        mock_open.return_value = mock_config_file
                        mock_serial_reader = MagicMock()
                        mock_serial.Serial.return_value = mock_serial_reader
                        mock_serial_reader.inWaiting.return_value = 0
                        get_serial("testing")
                        eq_(mock_serial_reader.inWaiting.call_count, 1)
                        eq_(mock_retriever.call_count, 0)


def test_get_configuration_unit():
    with patch("scripts.get_serial.open") as mock_open:
        with NamedTemporaryFile() as tmp:
            with open(tmp.name, "r+w") as mock_config_file:
                mock_config_file.write(MOCK_CONFIG_FILE)
                mock_config_file.flush()
                mock_config_file.seek(0)
                mock_open.return_value = mock_config_file
                config_dict = get_configuration("foo/bar")
                assert_dict_equal(
                    config_dict, {
                        "baudrate": 38400,
                        "tty_file": "foo/bar",
                        "data_path": "pi/mock/data",
                        "refresh_rate": 1000,
                        "vent_disconnect_tolerance": 1,
                    }
                )


def test_get_serial_on_vent_disconnect():
    with patch("scripts.get_serial.get_configuration") as get_config:
        with patch("scripts.get_serial.serial") as mock_serial:
            with patch("scripts.get_serial.open") as mock_open:
                with patch("scripts.get_serial.set_file_permissions"):
                    patched_config = copy(MOCK_CONFIG)
                    patched_config["refresh_rate"] = 1000  # An arbitrarily large number
                    get_config.return_value = patched_config
                    mock_file = MagicMock()
                    mock_open.return_value = mock_file
                    mock_serial_reader = MagicMock()
                    mock_serial_reader.readline.return_value = MOCK_SERIAL_RESPONSE
                    mock_serial.Serial.return_value = mock_serial_reader
                    mock_serial_reader.inWaiting.side_effect = lambda: vent_disc_iterator.next()
                    get_serial("testing")
                    last_line_written = mock_file.__enter__().write.call_args_list[-1][0][0]
                    eq_(last_line_written, MOCK_SERIAL_RESPONSE)
                    eq_(mock_open.call_count, 1)
                    # Writes once for the datetime, the next for the data
                    eq_(mock_file.__enter__().write.call_count, 2)


def test_get_serial_on_no_data_in_serial_buffer():
    with patch("scripts.get_serial.get_configuration") as get_config:
        with patch("scripts.get_serial.serial") as mock_serial:
            with patch("scripts.get_serial.open") as mock_open:
                with patch("scripts.get_serial.retrieve_data") as mock_retriever:
                    get_config.return_value = MOCK_CONFIG
                    mock_file = MagicMock()
                    mock_open.return_value = mock_file
                    mock_serial_reader = MagicMock()
                    mock_serial.Serial.return_value = mock_serial_reader
                    mock_serial_reader.inWaiting.return_value = 0
                    get_serial("testing")
                    eq_(mock_open.call_count, 0)
                    eq_(mock_serial_reader.inWaiting.call_count, 1)
                    eq_(mock_retriever.call_count, 0)


def test_get_serial_on_success():
    with patch("scripts.get_serial.get_configuration") as get_config:
        with patch("scripts.get_serial.serial") as mock_serial:
            with patch("scripts.get_serial.open") as mock_open:
                with patch("scripts.get_serial.set_file_permissions"):
                    get_config.return_value = MOCK_CONFIG
                    mock_file = MagicMock()
                    mock_serial_reader = MagicMock()
                    mock_serial_reader.readline.return_value = MOCK_SERIAL_RESPONSE
                    mock_open.return_value = mock_file
                    mock_serial.Serial.return_value = mock_serial_reader
                    get_serial("testing")
                    last_line_written = mock_file.__enter__().write.call_args_list[-1][0][0]
                    eq_(mock_open.call_count, 1)
                    eq_(last_line_written, MOCK_SERIAL_RESPONSE)
                    mock_serial.Serial.assert_called_once_with(
                        port=MOCK_CONFIG["tty_file"],
                        baudrate=MOCK_CONFIG["baudrate"]
                    )
