"""
Configure the Flask application.
"""
from logging.config import dictConfig

from clinicalsupervisor import defaults
from clinicalsupervisor.controllers import create_routes


def configure_app(app, debug=False, testing=False):
    """
    Load configuration and initialize collaborators.
    """

    app.debug = debug
    app.testing = testing

    _configure_from_defaults(app)
    _configure_from_environment(app)
    _configure_logging(app)

    create_routes(app)


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
