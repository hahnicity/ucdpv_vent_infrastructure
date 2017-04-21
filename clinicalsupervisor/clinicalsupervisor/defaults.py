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


# XXX Just turn this into a big dict in the future.
ARTIFICIAL_DNS_PROPS = {
    "start": "10.190.16.60",
    "exceptions": {
        "rpi26": "10.190.16.130",
        "rpi27": "10.190.16.85",
        "rpi28": "10.190.16.86",
        "rpi29": "10.190.16.87",
        "rpi30": "10.190.16.88",
        "rpi31": "10.190.16.89",
        "rpi37": "10.190.16.131",
        "rpi38": "10.190.16.132",
        "rpi39": "10.190.16.133",
        "rpi40": "10.190.16.134",
        "rpi41": "10.190.16.135",
        "rpi42": "10.190.16.136",
        "rpi43": "10.190.16.137",
        "rpi44": "10.190.16.138",
        "rpi45": "10.190.16.139",
        "rpi46": "10.190.16.140",
        "rpi47": "10.190.16.141",
        "rpi48": "10.190.16.142",
        "rpi49": "10.190.16.143",
        "rpi50": "10.190.16.144",
        "rpi51": "10.190.16.145",
        "rpi52": "10.190.16.146",
        "rpi53": "10.190.16.147",
        "rpi54": "10.190.16.148",
        "rpi55": "10.190.16.149",
        "rpi56": "10.190.16.150",
        "rpi57": "10.190.16.151",
        "rpi58": "10.190.16.152",
        "rpi59": "10.190.16.153",
        "rpi60": "10.190.16.154",
    },
    "no_pi_for": ["rpi36"],
    "pi_count": 35,  # goes from 1 - 35
    "unused": ["10.190.16.90"],
}


def setup_complete_artificial_dns():
    complete_dns_addrs = {"rpi1": ARTIFICIAL_DNS_PROPS["start"]}
    for k, v in ARTIFICIAL_DNS_PROPS["exceptions"].items():
        complete_dns_addrs[k] = v
    for i in range(2, ARTIFICIAL_DNS_PROPS["pi_count"] + 1):
        full_ip = "{}.{}".format("10.190.16", 60 + i - 1)
        if full_ip in ARTIFICIAL_DNS_PROPS["unused"]:
            continue
        rpi_hostname = "rpi{}".format(i)
        if rpi_hostname in  ARTIFICIAL_DNS_PROPS["exceptions"]:
            continue
        complete_dns_addrs[rpi_hostname] = full_ip
    return complete_dns_addrs


BACKUP_USER = "backup"
CLEAN_USER = "cleaner"
COMPLETE_ARTIFICIAL_DNS = setup_complete_artificial_dns()
DATA_DIR = "/home/pi/Data"
FINAL_PATIENT_DIR = "/Users/retriever"
LISTER_USER = "lister"
LOCAL_BACKUP_DIR = join(FINAL_PATIENT_DIR, "Data")
RSYNC_PATH = "/opt/local/bin/rsync"
SSH_OPTIONS = [
    "StrictHostKeyChecking=no",
    "ConnectTimeout=5",
    "Compression=yes",
    # Arcfour is less secure but the hospital network is quite slow. Since we
    # are working with non-PHI we can take the risk.
    "Ciphers=arcfour256,arcfour128,blowfish-cbc,aes128-cbc,aes128-ctr,aes256-ctr,3des-cbc",
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
