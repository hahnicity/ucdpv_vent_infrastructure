import ConfigParser
import datetime
import grp
import os
import pwd
import socket
import time

import serial


def get_configuration(filename):
    config_dict = {}
    with open(filename, "r") as file_:
        parser = ConfigParser.ConfigParser()
        parser.readfp(file_)
        config_dict["baudrate"] = parser.getint("config", "baudrate")
        config_dict["tty_file"] = parser.get("config", "tty_file")
        config_dict["data_path"] = parser.get("config", "data_path")
        config_dict["refresh_rate"] = parser.getint("config", "refresh_rate")
        config_dict["vent_disconnect_tolerance"] = parser.getint("config", "vent_disconnect_tolerance")
    return config_dict


def set_file_permissions(filename):
    uid = pwd.getpwnam("root").pw_uid
    gid = grp.getgrnam("pi").gr_gid
    os.chown(filename, uid, gid)
    os.chmod(filename, 0664)


def flush_serial_buffers(serial_reader):
    serial_reader.flushInput()
    serial_reader.flushOutput()


def retrieve_data(filename, config, serial_reader):
    """
    Retrieve data from the ventilator and write it to file
    """
    # open in binary mode
    with open(filename, "wb") as f:
        set_file_permissions(filename)
        now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f")
        f.write(now + '\n')
        # time starts when first file is made
        begin = int(datetime.datetime.now().strftime("%s"))
        elapsed = 0
        # This var tracks time in between breaths. Set this var to the current time.
        # Later if there have been no breaths then we will be able to catch it
        read_time_start = time.time()
        while elapsed < config["refresh_rate"]:
            elapsed = time.time() - begin
            if serial_reader.inWaiting() > 0:
                line = serial_reader.readline()
                f.write(line)
                f.flush()
                read_time_start = time.time()
            # If the time in between breaths is greater than some threshold then stop the file
            elif time.time() - read_time_start > config["vent_disconnect_tolerance"]:
                return


def get_serial(config_type):
    if config_type not in ["testing", "prod"]:
        raise Exception("Configuration type not valid. Choose either 'testing' or 'prod'")

    config_path = {
        "prod": "/etc/b2c/script_config",
        "testing": "/etc/b2c/script_testing_config"
    }[config_type]
    config = get_configuration(config_path)
    # open port, set baudrate
    ser = serial.Serial(port=config["tty_file"], baudrate=config["baudrate"])
    flush_serial_buffers(ser)
    while True:
        # Wait until we have something to collect. If not sleep momentarily
        if ser.inWaiting() == 0:
            time.sleep(0.1)
        else:
            now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f")
            filename = str(socket.gethostname() +  "-" + now)
            filename = os.path.join(os.path.abspath(config["data_path"]), filename)
            filename = filename + ".csv"
            retrieve_data(filename, config, ser)
            flush_serial_buffers(ser)  # not too sure why we want to have this behavior but ok

        if config_type == "testing":
            break
