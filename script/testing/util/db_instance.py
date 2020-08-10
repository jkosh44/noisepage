#!/usr/bin/python3
import os
import signal
import socket
import subprocess
import sys
import time
import traceback

from util import constants
from util.common import *
from util.constants import LOG


class DbInstance:
    """ Class to represent a single DB instance """

    def __init__(self, db_host, db_path, db_port, db_output_file):
        self.db_host = db_host
        self.db_path = db_path
        self.db_port = db_port
        self.db_output_file = db_output_file
        self.db_output_fd = None
        self.db_process = None

    def run_db(self):
        """ Start the DB instance """

        # Allow ourselves to try to restart the DBMS multiple times
        for attempt in range(constants.DB_START_ATTEMPTS):
            # Kill any other terrier processes that our listening on our target port
            for other_pid in check_port(self.db_port):
                LOG.info(
                    f"Killing existing server instance listening on port {self.db_port} [PID={other_pid}]")
                os.kill(other_pid, signal.SIGKILL)
            # FOR

            self.db_output_fd = open(self.db_output_file, "w+")
            self.db_process = subprocess.Popen([self.db_path, "-port", str(self.db_port)],
                                               stdout=self.db_output_fd,
                                               stderr=self.db_output_fd)
            try:
                self.wait_for_db()
                break
            except:
                self.stop_db()
                # TODO use Ben's new logging function
                LOG.error("+" * 100)
                LOG.error("DATABASE OUTPUT")
                print_output(self.db_output_file)
                if attempt + 1 == constants.DB_START_ATTEMPTS:
                    raise
                traceback.print_exc(file=sys.stdout)
                pass
        # FOR
        return

    def wait_for_db(self):
        """ Wait for the db instance to come up """

        # Check that PID is running
        if not check_pid(self.db_process.pid):
            raise RuntimeError(f"Unable to find DBMS PID {self.db_process.pid}")

        # Wait a bit before checking if we can connect to give the system time to setup
        time.sleep(constants.DB_START_WAIT)

        # flag to check if the db is running
        is_db_running = False

        # Keep trying to connect to the DBMS until we run out of attempts or we succeed
        for i in range(constants.DB_CONNECT_ATTEMPTS):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((self.db_host, int(self.db_port)))
                s.close()
                LOG.info(f"Connected to server in {i * constants.DB_CONNECT_SLEEP} seconds [PID={self.db_process.pid}]")
                is_db_running = True
                break
            except:
                if i > 0 and i % 20 == 0:
                    LOG.error(f"Failed to connect to DB server [Attempt #{i}/{constants.DB_CONNECT_ATTEMPTS}]")
                    # os.system('ps aux | grep terrier | grep {}'.format(self.db_process.pid))
                    # os.system('lsof -i :15721')
                    traceback.print_exc(file=sys.stdout)
                time.sleep(constants.DB_CONNECT_SLEEP)
                continue

        if not is_db_running:
            status = "RUNNING"
            if not check_pid(self.db_process.pid):
                status = "NOT RUNNING"
            msg = f"Unable to connect to DBMS [PID={self.db_process.pid} / {status}]"
            raise RuntimeError(msg)
        return

    def stop_db(self):
        """ Stop the Db instance and print it's log file """
        if not self.db_process:
            return

        # get exit code, if any
        self.db_process.poll()
        if self.db_process.returncode is not None:
            # Db terminated already
            self.db_output_fd.close()
            print_output(self.db_output_file)
            msg = f"DB terminated with return code {self.db_process.returncode}"
            raise RuntimeError(msg)

        # still (correctly) running, terminate it
        self.db_process.terminate()
        self.db_process = None

        return
