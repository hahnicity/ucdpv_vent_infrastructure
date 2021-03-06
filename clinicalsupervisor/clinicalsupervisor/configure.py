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
Configure the Flask application.
"""
from logging.config import dictConfig

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from clinicalsupervisor import defaults
from clinicalsupervisor.controllers import create_routes
from clinicalsupervisor.db.schema import metadata


class MockDB(object):
    name = 'mock'


def create_db(app):
    db = create_engine(app.config['DB_URL'])
    try:
        metadata.create_all(db)
        app.logger.info("Connected to database")
    except OperationalError as err:
        if app.config['RAISE_ERROR_IF_NO_MYSQL_CONN']:
            app.logger.error("Unable to connect to database!")
            raise err
        else:
            db = MockDB()
    return db


def configure_app(app, debug=False, testing=False):
    """
    Load configuration and initialize collaborators.
    """

    app.debug = debug
    app.testing = testing

    _configure_from_defaults(app)
    _configure_from_environment(app)
    _configure_logging(app)

    db = create_db(app)
    create_routes(app, db)


def _configure_from_defaults(app):
    """
    Load configuration defaults from defaults.py in this package.
    """
    app.config.from_object(defaults)


def _configure_from_environment(app):
    """
    Load configuration from a file specified as the value of
    the CHEDDAR_SETTINGS environment variable.

    Don't complain if the variable is unset.
    """
    app.config.from_envvar("CLINICALSUPERVISOR_SETTINGS", silent=True)


def _configure_logging(app):
    if app.debug or app.testing:
        app.config['LOGGING']['loggers']['']['handlers'] = ['console']
        if 'app' in app.config['LOGGING']['handlers']:
            del app.config['LOGGING']['handlers']['app']

    dictConfig(app.config['LOGGING'])
