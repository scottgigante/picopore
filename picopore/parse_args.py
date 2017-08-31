"""
    This file is part of Picopore.

    Picopore is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Picopore is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Picopore.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import subprocess
import warnings

from argparse import ArgumentParser, ArgumentError, Action, RawDescriptionHelpFormatter
from builtins import input

from picopore.version import __version__

def checkDeprecatedArgs():
    args = sys.argv[1:]
    try:
        if "--realtime" in args:
            args.remove('--realtime')
            warnings.warn("picopore --realtime will be deprecated in 1.3.0. Use picopore-realtime instead.",FutureWarning)
            exit(subprocess.call(['picopore-realtime'] + args))
        if "--test" in args:
            args.remove('--test')
            warnings.warn("picopore --test will be deprecated in 1.3.0. Use picopore-test instead.",FutureWarning)
            exit(subprocess.call(['picopore-test'] + args))
    except KeyboardInterrupt:
        exit(0)

def checkInputs(args):
    args.input = [os.path.abspath(i) for i in args.input]
    # we go recursively - better remove duplicates
    keepDirs = []
    for i in range(len(args.input)):
        subDir = False
        for j in range(len(args.input)):
            if args.input[j] in args.input[i] and i != j:
                subDir = True
        if not subDir:
            keepDirs.append(args.input[i])
    return keepDirs

def checkSure():
    response = input("Are you sure? (yes|no): ")
    assert isinstance(response, str)
    if "yes".startswith(response):
        return 1
    else:
        return 0

class AutoBool(Action):
    def __init__(self, option_strings, dest, default=None, required=False, help=None):
        """Automagically create --foo / --no-foo argument pairs
        Source: https://github.com/nanoporetech/nanonet/blob/master/nanonet/cmdargs.py"""

        if default is None:
            raise ValueError('You must provide a default with AutoBool action')
        if len(option_strings)!=1:
            raise ValueError('Only single argument is allowed with AutoBool action')
        opt = option_strings[0]
        if not opt.startswith('--'):
            raise ValueError('AutoBool arguments must be prefixed with --')

        opt = opt[2:]
        opts = ['--' + opt, '--no-' + opt]
        if default:
            default_opt = opts[0]
        else:
            default_opt = opts[1]
        super(AutoBool, self).__init__(opts, dest, nargs=0, const=None,
                                       default=default, required=required,
                                       help='{} (Default: {})'.format(help, default_opt))
    def __call__(self, parser, namespace, values, option_strings=None):
        if option_strings.startswith('--no-'):
            setattr(namespace, self.dest, False)
        else:
            setattr(namespace, self.dest, True)

def addCommonArgs(parser):
    parser.add_argument('-v', '--version', action='version', version='Picopore {}'.format(__version__), help="show version number and exit")
    parser.add_argument("-y", action="store_true", default=False, help="skip confirm step")
    parser.add_argument("-t", "--threads", type=int, default=1, help="number of threads (Default: 1)", metavar="INT")
    parser.add_argument("--prefix", default=None, help="add prefix to output files to prevent overwrite", metavar="STR")
    parser.add_argument("--skip-root", action=AutoBool, default=False, help="ignore files in root input directories for albacore realtime compression")
    parser.add_argument("--print-every", type=int, default=100, help="print a dot every approximately INT files, or -1 to silence (Default: 100)", metavar="INT")
    parser.add_argument("input", nargs="*", help="list of directories or fast5 files to shrink")
    return parser

__description = """A tool for reducing the size of an Oxford Nanopore Technologies dataset without losing any data"""
def parseArgs(description=None, prog='picopore'):
    checkDeprecatedArgs()
    if description is not None:
        description = __description + "\n\n" + description
    else:
        description = __description
    parser = ArgumentParser(description=description, prog=prog, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=('lossless', 'deep-lossless', 'raw'), help="choose compression mode", required=True)
    parser.add_argument("--revert", default=False, action="store_true", help="reverts files to original size (lossless modes only)")
    parser.add_argument("--fastq", action=AutoBool, default=True, help="retain FASTQ data (raw mode only)")
    parser.add_argument("--summary", action=AutoBool, default=False, help="retain summary data (raw mode only)")
    parser.add_argument("--manual", default=None, help="manually remove only groups whose paths contain STR (raw mode only, regular expressions permitted, overrides defaults)", metavar="STR")
    parser = addCommonArgs(parser)
    args = parser.parse_args()

    args.input = checkInputs(args)
    args.group = "all" # TODO: is it worth supporting group?

    return args

def parseRenameArgs(description, prog='picopore-rename'):
    parser = ArgumentParser(description=description, prog=prog)
    parser.add_argument('-p', '--pattern', required=True, help="String or regex to replace")
    parser.add_argument('-r', '--replacement', required=True, help="String or regex replacement for PATTERN")
    parser = addCommonArgs(parser)
    args = parser.parse_args()

    return args
