#!/usr/bin/python3
import argparse
import errno
import os
import re
import shlex
import subprocess

from util.constants import LOG


def run_command(command,
                error_msg="",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=None):
    """
    General purpose wrapper for running a subprocess
    """
    p = subprocess.Popen(shlex.split(command),
                         stdout=stdout,
                         stderr=stderr,
                         cwd=cwd)

    while p.poll() is None:
        if stdout == subprocess.PIPE:
            out = p.stdout.readline()
            if out:
                LOG.info(out.decode("utf-8").rstrip("\n"))

    rc = p.poll()
    return rc, p.stdout, p.stderr


def check_port(port):
    """Get the list of PIDs (if any) listening on the target port"""

    # Copied from https://gist.github.com/jossef/593ade757881bb7ddfe0
    # I would like to use psutil to make this more portable but that would require
    # us to install an additional package with pip

    command = "lsof -i :%s | awk '{print $2}'" % port
    output = subprocess.check_output(command, shell=True).strip()
    if output:
        output = re.sub(' +', ' ', output.decode('utf-8'))
        for pid in output.split('\n'):
            try:
                yield int(pid)
            except:
                pass


def check_pid(pid):
    """Check whether pid exists in the current process table."""

    # Copied from psutil
    # https://github.com/giampaolo/psutil/blob/5ba055a8e514698058589d3b615d408767a6e330/psutil/_psposix.py#L28-L53

    if pid == 0:
        return True
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH) therefore we should never get
            # here. If we do let's be explicit in considering this
            # an error.
            raise err
    else:
        return True


def print_output(filename):
    """ Print out contents of a file """
    fd = open(filename)
    lines = fd.readlines()
    for line in lines:
        LOG.info(line.strip())
    fd.close()
    return


def parse_common_command_line_args(description):
    '''Common command line argument parsing methods'''

    aparser = argparse.ArgumentParser(description=description)
    aparser.add_argument("--db-host", help="DB Hostname")
    aparser.add_argument("--db-port", type=int, help="DB Port")
    aparser.add_argument("--db-replica-port", type=int, help="DB Replica Ports", nargs='*')
    aparser.add_argument("--db-output-file", help="DB output log file")
    aparser.add_argument("--db-replica-output-file", help="DB Replica output log files", nargs='*')
    aparser.add_argument("--build-type",
                         default="debug",
                         choices=["debug", "release", "relwithdebinfo"],
                         help="Build type (default: %(default)s)")
    return aparser
