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
import json
from multiprocessing import Process
import os
from subprocess import PIPE, Popen
import traceback

from flask import jsonify, render_template, request

from clinicalsupervisor.db.csv_reader import extract_raw
from clinicalsupervisor.db.dbops import raw_vwd_to_db


def load_files_to_db(app, db, chunksize, files, patient):
    """
    Send collected and attributed vwd to a database
    """
    if db.name != 'mock':
        for file in files:
            try:
                gen = extract_raw(open(file, 'rU'), False)
                raw_vwd_to_db(db, chunksize, gen, patient)
            except Exception as err:
                app.logger.error(traceback.format_exc())


def clean_rpis(app, regular_ssh_options, name, files):
    """
    Clean out all files in the data directory
    """
    try:
        ip = app.config["COMPLETE_ARTIFICIAL_DNS"][name]
    except KeyError:
        ip = name

    batch = files[:1000]
    idx = 1
    while batch:
        cmd = regular_ssh_options + ["{}@{}".format(app.config["CLEAN_USER"], ip), "rm"] + batch
        app.logger.debug("Running ssh command {}".format(cmd))
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        batch = files[1000 * idx:1000 * (idx + 1)]
        idx += 1
    return stdout, stderr, proc.returncode


def make_initial_move_file_paths(app, name, basenames):
    """
    Return the string of paths where our backups final resting locations will
    be

    Takes the name of the rpi and the basenames of all files to move
    """
    files = []
    for file in basenames:
        files.append(os.path.join(app.config["LOCAL_BACKUP_DIR"], name, file))
    return files


def move_files(app, db, name, files, pseudo_id):
    """
    Once patient rpi files are backed up move them to their appropriate
    resting directory location. The will be a determinant of the rpi name
    and the patient pseudo id
    """
    resting_dir = os.path.join(app.config["FINAL_PATIENT_DIR"], pseudo_id)
    # Use -p to ensure that if the directory exists we don't fail
    create_dir_cmd = ["mkdir", "-p", resting_dir]
    app.logger.debug("Create local dir with cmd {}".format(create_dir_cmd))
    proc = Popen(create_dir_cmd, stderr=PIPE, stdout=PIPE)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        return stdout, stderr, proc.returncode
    initial_paths = make_initial_move_file_paths(app, name, files)
    final_paths = []
    for path in initial_paths:
        final_path = os.path.join(resting_dir, "{}-{}".format(pseudo_id, os.path.basename(path)))
        move_file_cmd = ["mv", path, final_path]
        final_paths.append(final_path)
        app.logger.debug("Move files to resting dir with cmd {}".format(move_file_cmd))
        proc = Popen(move_file_cmd, stderr=PIPE, stdout=PIPE)
        proc.communicate()
        if proc.returncode != 0:
            return stdout, stderr, proc.returncode
    p = Process(target=load_files_to_db, args=(app, db, app.config['CHUNKSIZE'], final_paths, pseudo_id))
    p.start()
    return stdout, stderr, proc.returncode


def create_routes(app, db):

    rsync_ssh_options = "ssh -o {}".format(" -o ".join(app.config["SSH_OPTIONS"]))
    regular_ssh_options = ["ssh"]
    for option in app.config["SSH_OPTIONS"]:
        regular_ssh_options.append("-o")
        regular_ssh_options.append(option)

    def make_clean_files_paths(basenames):
        files = []
        for file in basenames:
            files.append(os.path.join(app.config["DATA_DIR"], file))
        return files

    @app.route("{}/".format(app.config["URL_PATH"]))
    def index():
        """
        Index page: show recent history.
        """
        app.logger.debug("Showing index page")
        return render_template("index.html", url_path=app.config["URL_PATH"])

    @app.route("{}/backups/".format(app.config["URL_PATH"]))
    def backups():
        """
        Backups page: this is where we go to backup raspberry pi's
        """
        app.logger.debug("Showing backups page")
        return render_template("backups.html", api_name="backup", url_path=app.config["URL_PATH"])

    @app.route("{}/cleanall/".format(app.config["URL_PATH"]))
    def clean():
        """
        Clean page: Remove all data for raspberry pi's here
        """
        app.logger.debug("Showing clean all files rpi page")
        return render_template("cleanall.html", api_name="cleanall", url_path=app.config["URL_PATH"])

    @app.route("{}/enroll/".format(app.config["URL_PATH"]))
    def enroll():
        """
        Enroll page: Collect data from raspberry pi
        """
        app.logger.debug("Showing enroll page")
        return render_template("enroll.html", api_name="enroll", url_path=app.config["URL_PATH"])

    @app.route("{}/list_only/".format(app.config["URL_PATH"]))
    def listonly_input():
        """
        List page: Only list files on the pi
        """
        app.logger.debug("Showing listing page")
        return render_template("listonly_input.html", api_name="list_only", url_path=app.config["URL_PATH"])

    @app.route("{}/backup/<name>/".format(app.config["URL_PATH"]))
    def backup_rpi(name):
        """
        Backup the raspberry pi into a configurable directory.

        Takes one argument, the raspberry pi hostname.
        """
        try:
            ip = app.config["COMPLETE_ARTIFICIAL_DNS"][name]
        except KeyError:
            ip = name
        cmd = [
            app.config["RSYNC_PATH"],
            "-re",
            rsync_ssh_options,
            "{}@{}:{}/*".format(app.config["BACKUP_USER"], ip, app.config["DATA_DIR"]),
            "{}/{}".format(app.config["LOCAL_BACKUP_DIR"], name)
        ]
        app.logger.debug("Running ssh command {}".format(cmd))
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            return "Could not backup {} {}".format(name, stderr), 500
        return "Successfully backed up {}".format(name), 200

    @app.route("{}/cleanall/<name>/".format(app.config["URL_PATH"]))
    def cleanall(name):
        """
        Remove all data from the raspberry pi data directory

        Takes one argument: raspberry pi hostname
        """
        output, code = list_files(name)
        if code != 200:
            return output, code
        fullpaths = make_clean_files_paths(json.loads(output)["files"])
        _, stderr, rc = clean_rpis(app, regular_ssh_options, name, fullpaths)
        if rc != 0:
            return stderr, 500
        return "Cleaned all data files from {}".format(name), 200


    @app.route("{}/enroll/<name>/".format(app.config["URL_PATH"]))
    def enroll_patient(name):
        """
        Backup, clean, and move backed up files to a final resting place

        Takes one argument: raspberry pi hostname
        """
        # If we want another minor speed bump we can implement ssh multiplexing
        # with ControlMaster. But we need to implement 3 separate threads to
        # begin the multiplexed connections
        output, rc = backup_rpi(name)
        if rc != 200:
            return output, rc
        output, rc = list_files(name)
        if rc != 200:
            return output, rc
        return render_template("finalize.html", files=json.loads(output)["files"], url_path=app.config["URL_PATH"])

    @app.route("{}/enroll/<name>/finalize".format(app.config["URL_PATH"]), methods=["POST"])
    def enroll_finalization(name):
        """
        Take the files we wish to delete and then remove them

        Takes one argument: raspberry pi hostname
        """
        # 0 corresponds to get the list of pseudo_ids
        # the other 0 is for the actual pseudo id
        # It looks like this [[<pseudo_id>], [<file1>, <file2>, ...]]
        pseudo_id = request.form.listvalues()[0][0]
        if not pseudo_id:
            return "You must fill out the patient pseudo id!", 400
        # The 1 corresponds to file inputs
        basenames = request.form.listvalues()[1]
        if not basenames:
            return "You must select files to attach to a patient!", 400
        stdout, stderr, rc = move_files(app, db, name, basenames, pseudo_id)
        if rc != 0:
            return "Unable to properly move backed up files to pseudo id dir {}".format(stderr), 500
        files = make_clean_files_paths(basenames)
        stdout, stderr, rc = clean_rpis(app, regular_ssh_options, name, files)
        if rc != 0:
            return "Unable to remove files from {} {}".format(name, stderr)
        return render_template("index.html", url_path=app.config["URL_PATH"])

    @app.route("{}/list_only/<name>/".format(app.config["URL_PATH"]))
    def listonly_show(name):
        """
        Only list files in the raspberry pi data dir. Then render html template showing
        what the files are

        Takes one argument: raspberry pi hostname
        """
        output, code = list_files(name)
        if code != 200:
            return output, code
        return render_template("listonly_show.html", files=json.loads(output)["files"], url_path=app.config["URL_PATH"])

    @app.route("{}/listfiles/<name>/".format(app.config["URL_PATH"]))
    def list_files(name):
        """
        Only list files in the raspberry pi data dir. Doesn't render html template,
        just returns a JSON blob

        Takes one argument: raspberry pi hostname
        """
        try:
            ip = app.config["COMPLETE_ARTIFICIAL_DNS"][name]
        except KeyError:
            ip = name
        cmd = regular_ssh_options + ["{}@{}".format(app.config["LISTER_USER"], ip)]
        app.logger.debug("Running ssh command {}".format(cmd))
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            return "Could not list files on {} {}".format(name, stderr), 500
        response = {"name": name, "files": filter(lambda x: x, stdout.split("\n"))}
        return json.dumps(response), 200
