# I know this might not be the best of plans but it saves code duplication
from clinicalsupervisor.defaults import COMPLETE_ARTIFICIAL_DNS


def find_home_dir_root(distribution):
    if distribution == "MacOSX":
        return "/Users"
    else:
        return "/home"


def get_all_hostnames(rpi_ip_map):
    hostnames = [rpi["hostname"] for rpi in rpi_ip_map]
    return ",".join(hostnames)


def get_rpi_ip_addr(rpi_name):
    return COMPLETE_ARTIFICIAL_DNS[rpi_name]


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
            "get_rpi_ip_addr": get_rpi_ip_addr,
            "if_bash": if_bash,
            "set_backup_crontab_minute": set_backup_crontab_minute,
        }
