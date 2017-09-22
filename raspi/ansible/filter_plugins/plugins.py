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

def get_nginx_root_dir(distribution):
    if distribution == "MacOSX":
        return "/usr/local/etc/"
    else:
        return "/etc/"


def get_clinicalsupervisor_dir(distribution):
    if distribution == "MacOSX":
        return "/Applications"
    else:
        return "/opt"


def find_home_dir_root(distribution):
    if distribution == "MacOSX":
        return "/Users"
    else:
        return "/home"


def get_all_hostnames(rpi_ip_map):
    hostnames = [rpi["hostname"] for rpi in rpi_ip_map]
    return ",".join(hostnames)


def get_rpi_ip_addr(rpi_name, hostname_map={}):
    return hostname_map.get(rpi_name, rpi_name)


def if_bash(users):
    listed = []
    for user in users:
        try:
            type_ = user["shell"]
        except KeyError:
            listed.append(user)
            continue
        if type_ not in ["/bin/sh"]:
            listed.append(user)
    return listed


def set_backup_crontab_minute(hostname):
    rpi_number = int(hostname.strip("rpi"))
    return (rpi_number - 1) % 60


class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            "find_home_dir_root": find_home_dir_root,
            "get_all_hostnames": get_all_hostnames,
            "get_clinicalsupervisor_dir": get_clinicalsupervisor_dir,
            "get_nginx_root_dir": get_nginx_root_dir,
            "get_rpi_ip_addr": get_rpi_ip_addr,
            "if_bash": if_bash,
            "set_backup_crontab_minute": set_backup_crontab_minute,
        }
