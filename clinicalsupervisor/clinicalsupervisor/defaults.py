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
Default configuration values.
"""
from os.path import join


BACKUP_USER = "backup"
CLEAN_USER = "cleaner"
COMPLETE_ARTIFICIAL_DNS = {
    # This needs to be set up by either manual config or ansible
    # hostnames should look like
    #
    # "rpi1": "192.168.1.2",
    # "rpi2": "192.168.1.3",
    # ...
}
CHUNKSIZE = 1000
DATA_DIR = "/home/pi/Data"
DB_URL = "mysql://root:root@localhost/vwd"
FINAL_PATIENT_DIR = "/home/retriever"
JUNKYARD_DIR = '/home/retriever/junkyard'
LISTER_USER = "lister"
LOCAL_BACKUP_DIR = join(FINAL_PATIENT_DIR, "Data")
RAISE_ERROR_IF_NO_MYSQL_CONN = False
RSYNC_PATH = "/opt/local/bin/rsync"
SSH_OPTIONS = [
    "StrictHostKeyChecking=no",
    "ConnectTimeout=5",
]
URL_PATH = ""

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'debug': {
            'format': '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
            'datefmt': '%Y%m%d',
        },
        'default': {
            'format': '%(asctime)s - %(levelname)s - %(message)s',
            'datefmt': '%Y%m%d',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'debug',
            'stream': 'ext://sys.stdout',
        },
        'app': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'default',
            'filename': '/var/log/clinicalsupervisor/clinicalsupervisor.log',
        },
    },

    'loggers': {
        '': {
            'handlers': ['console', 'app'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}
