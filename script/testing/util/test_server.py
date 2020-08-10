#!/usr/bin/python3
import os
import sys
import traceback

from util import constants
from util.common import *
from util.db_instance import DbInstance
from util.test_case import TestCase


class TestServer:
    """ Class to run general tests """

    def __init__(self, args):
        """ Locations and misc. variable initialization """
        # clean up the command line args
        self.args = {k: v for k, v in args.items() if v}

        # set the DB path
        self.set_db_path()

        # db server location
        self.db_host = self.args.get("db_host", constants.DEFAULT_DB_HOST)

        # set up main db instance
        db_port = self.args.get("db_port", constants.DEFAULT_DB_PORT)
        db_output_file = self.args.get("db_output_file",
                                       constants.DEFAULT_DB_OUTPUT_FILE)
        self.main_db_instance = DbInstance(self.db_host, self.db_path, db_port, db_output_file)

        # set up replica db instance
        # TODO support multiple replicas
        db_replica_port = self.args.get("db_replica_port", constants.DEFAULT_DB_REPLICA_PORT)
        db_replica_output_file = self.args.get("db_replica_output_file",
                                               constants.DEFAULT_DB_REPLICA_OUTPUT_FILE)
        self.replica_db_instance = DbInstance(self.db_host, self.db_path, db_replica_port, db_replica_output_file)

        return

    def run_pre_suite(self):
        pass

    def run_post_suite(self):
        pass

    def set_db_path(self):
        """ location of db server, relative to this script """

        # builds on Jenkins are in build/<build_type>
        # but CLion creates cmake-build-<build_type>/<build_type>
        # determine what we have and set the server path accordingly
        bin_name = constants.DEFAULT_DB_BIN
        build_type = self.args.get("build_type", "")
        path_list = [
            os.path.join(constants.DIR_REPO, "build", build_type),
            os.path.join(constants.DIR_REPO,
                         "cmake-build-{}".format(build_type), build_type)
        ]
        for dir in path_list:
            path = os.path.join(dir, bin_name)
            if os.path.exists(path):
                self.db_path = path
                return

        msg = "No DB binary found in {}".format(path_list)
        raise RuntimeError(msg)

    def check_db_binary(self):
        """ Check that a Db binary is available """
        if not os.path.exists(self.db_path):
            abs_path = os.path.abspath(self.db_path)
            msg = "No DB binary found at {}".format(abs_path)
            raise RuntimeError(msg)
        return

    def run_db(self):
        """ Start the DB server """
        self.main_db_instance.run_db()
        self.replica_db_instance.run_db()

    def stop_db(self):
        """ Stop the Db server and print it's log file """
        self.main_db_instance.stop_db()
        self.replica_db_instance.stop_db()

    def restart_db(self):
        """ Restart the DB """
        self.stop_db()
        self.run_db()

    def run_test(self, test_case: TestCase):
        """ Run the tests """
        if not test_case.test_command or not test_case.test_command_cwd:
            msg = "test command should be provided"
            raise RuntimeError(msg)

            # run the pre test tasks
        test_case.run_pre_test()

        # run the actual test
        self.test_output_fd = open(test_case.test_output_file, "w+")
        ret_val, _, _ = run_command(test_case.test_command,
                                    test_case.test_error_msg,
                                    stdout=self.test_output_fd,
                                    stderr=self.test_output_fd,
                                    cwd=test_case.test_command_cwd)
        self.test_output_fd.close()

        # run the post test tasks
        test_case.run_post_test()

        return ret_val

    def run(self, test_suite):
        """ Orchestrate the overall test execution """
        if type(test_suite) is not list: test_suite = [test_suite]
        ret_val_test_suite = None
        try:
            self.check_db_binary()
            self.run_pre_suite()

            # store each test case's result
            ret_val_list_test_case = {}
            for test_case in test_suite:
                if test_case.db_restart:
                    # for each test case, it can tell the test server whether it wants a fersh db or a used one
                    self.restart_db()
                # if there is not running db instance, we create one
                else:
                    if not self.main_db_instance.db_process:
                        self.main_db_instance.run_db()
                    if not self.replica_db_instance.db_process:
                        self.replica_db_instance.run_db()

                ret_val = self.run_test(test_case)

                print_output(test_case.test_output_file)

                ret_val_list_test_case[test_case] = ret_val

            # parse all test cases result
            # currently, we only want to know if there is an error one
            for test_case, test_result in ret_val_list_test_case.items():
                if test_result is None or test_result != constants.ErrorCode.SUCCESS:
                    ret_val_test_suite = constants.ErrorCode.ERROR
                    break
            else:
                # loop fell through without finding an error
                ret_val_test_suite = constants.ErrorCode.SUCCESS
        except:
            traceback.print_exc(file=sys.stdout)
            ret_val_test_suite = constants.ErrorCode.ERROR
        finally:
            # after the test suite finish, stop the database instance
            self.stop_db()

        if ret_val_test_suite is None or ret_val_test_suite != constants.ErrorCode.SUCCESS:
            # print the db log file, only if we had a failure
            print_output(self.main_db_instance.db_output_file)
            print_output(self.replica_db_instance.db_output_file)
        return ret_val_test_suite
