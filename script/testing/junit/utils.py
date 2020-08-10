#!/usr/bin/python3

from util.common import parse_common_command_line_args


def parse_command_line_args():
    '''Command line argument parsing methods'''

    aparser = parse_common_command_line_args("junit runner")

    aparser.add_argument("--test-output-file", help="Test output log file")
    aparser.add_argument("--query-mode",
                         choices=["simple", "extended"],
                         help="Query protocol mode")
    aparser.add_argument("--prepare-threshold",
                         type=int,
                         help="Threshold under the 'extended' query mode")

    args = vars(aparser.parse_args())

    return args
