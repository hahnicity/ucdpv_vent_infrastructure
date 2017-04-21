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
from os.path import join

from flask.ext.testing import TestCase
from mock import Mock, patch
from nose.tools import eq_

from clinicalsupervisor.app import create_app
from clinicalsupervisor.controllers import clean_rpis, move_files
from clinicalsupervisor.defaults import COMPLETE_ARTIFICIAL_DNS

CLEAN_USER = "cleaner"
SSH_OPTIONS = []
TEST_RPI = "rpiX"
TEST_RPI_IP = "10.10.10.10"


class MockApp(object):
    config = {
        "CLEAN_USER": CLEAN_USER,
        "COMPLETE_ARTIFICIAL_DNS": {TEST_RPI: TEST_RPI_IP},
        "LOCAL_BACKUP_DIR": "/bar/baz",
        "FINAL_PATIENT_DIR": "/bar",
    }
    logger = Mock()


class TestControllers(TestCase):
    def create_app(self):
        self.app = create_app(debug=True, testing=True)
        self.regular_ssh_options = ["ssh"]
        for option in self.app.config["SSH_OPTIONS"]:
            self.regular_ssh_options.append("-o")
            self.regular_ssh_options.append(option)
        return self.app

    def test_move_files(self):
        with patch("clinicalsupervisor.controllers.Popen") as mock_popen:
            mock_popen().communicate.return_value = ('', '')  # Stands for success
            mock_popen().returncode = 0
            mock_app = MockApp()
            mock_name = "rpi-mock"
            mock_pseudo_id = "11111"
            files = ["foo", "bar"]
            move_files(mock_app, mock_name, files, mock_pseudo_id)
            eq_(mock_popen.call_args_list[-2][0][0],
                ['mv', '/bar/baz/rpi-mock/foo', join(mock_app.config["FINAL_PATIENT_DIR"], '11111/11111-foo')])
            eq_(mock_popen.call_args_list[-1][0][0],
                ['mv', '/bar/baz/rpi-mock/bar', join(mock_app.config["FINAL_PATIENT_DIR"], '11111/11111-bar')])

    def test_list_files(self):
        with patch("clinicalsupervisor.controllers.Popen") as mock_popen:
            mock_popen().communicate.return_value = ('foo\nbar', '')  # Stands for success
            mock_popen().returncode = 0
            expected_clean_cmd = self.regular_ssh_options + ["lister@10.190.16.91"]
            response = self.client.get("/listfiles/rpi32/")
            eq_(mock_popen.call_args_list[-1][0][0], expected_clean_cmd)
            eq_(response.json, {"name": "rpi32", "files": ["foo", "bar"]})

    def test_clean_rpis(self):
        with patch("clinicalsupervisor.controllers.Popen") as mock_popen:
            mock_popen().communicate.return_value = "", ""
            mock_popen().returncode = 0
            files = map(lambda x: str(x), range(1001))
            app = MockApp()
            clean_rpis(app, SSH_OPTIONS, TEST_RPI, files)
            eq_(mock_popen.call_args_list[-2][0][0],
                ["{}@{}".format(CLEAN_USER, TEST_RPI_IP), "rm"] + files[0:1000])
            eq_(mock_popen.call_args_list[-1][0][0],
                ["{}@{}".format(CLEAN_USER, TEST_RPI_IP), "rm"] + files[1000:])
