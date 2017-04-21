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
Run a development server.
"""
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from clinicalsupervisor.app import create_app


def main():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-a',
                        dest='all_interfaces',
                        action='store_true',
                        default=False,
                        help='Listen on all interfaces')
    parser.add_argument('-p',
                        dest='port',
                        type=int,
                        default=5000,
                        help='Listen port')
    args, extra = parser.parse_known_args()

    app = create_app(debug=True)

    if args.all_interfaces:
        app.run(host='0.0.0.0',
                port=args.port)
    else:
        app.run(port=args.port)
