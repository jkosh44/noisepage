#!/usr/bin/python3

from oltpbench import constants
from util.common import parse_common_command_line_args


def parse_command_line_args():
    '''Command line argument parsing methods'''

    aparser = parse_common_command_line_args("Timeseries")

    aparser.add_argument(
        "--config-file", help="File containing a collection of test cases")

    public_report_server_list = constants.PERFORMANCE_STORAGE_SERVICE_API.keys()
    aparser.add_argument("--publish-results",
                         default="none",
                         choices=public_report_server_list,
                         help="Stores performance results in TimeScaleDB")
    aparser.add_argument("--publish-username",
                         default="none",
                         help="Publish Username")
    aparser.add_argument("--publish-password",
                         default="none",
                         help="Publish password")

    args = vars(aparser.parse_args())

    return args
