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

from argparse import ArgumentParser, ArgumentError
import os

from version import __version__
from util import log

def checkTestMode(test, args):
	if args.test:
		if "lossless" not in args.mode:
			raise ArgumentError(test, "{} mode not reversible by Picopore. Test cancelled.".format(args.mode))
		args.prefix = "picopore.test"
	return args.test

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

def checkRealtime(args):
	if args.realtime:
		log("Performing real time {} compression. ".format(args.mode),end='')
		if args.y:
			print('')
			return True
		elif checkSure():
			args.y = True
			return True
		else:
			return False

def parseArgs():
	parser = ArgumentParser(description="A tool for reducing the size of an Oxford Nanopore Technologies dataset without losing any data", prog="picopore")
	parser.add_argument('-v', '--version', action='version', version='Picopore {}'.format(__version__), help="show version number and exit")
	parser.add_argument("-y", action="store_true", default=False, help="skip confirm step")
	parser.add_argument("--revert", default=False, action="store_true", help="reverts files to original size (lossless modes only)")
	mut_excl = parser.add_mutually_exclusive_group(title="Lossless compression options:")
	mut_excl.add_argument("--realtime", default=False, action="store_true", help="monitor a directory for new reads and compress them in real time")
	test = mut_excl.add_argument("--test", default=False, action="store_true", help="compress to a temporary file and check that all datasets and attributes are equal (lossless modes only)")
	fastq_group = parser.add_mutually_exclusive_group()
	fastq_group.add_argument("--with-fastq", action="store_true", dest="fastq", default=True, help="retain FASTQ data (raw mode only)")
	fastq_group.add_argument("--no-fastq", action="store_false", dest="fastq", help="remove FASTQ data (raw mode only)")
	summary_group = parser.add_mutually_exclusive_group()
	summary_group.add_argument("--with-summary", action="store_true", dest="summary", default=True, help="retain basecalling summary data (raw mode only)")
	summary_group.add_argument("--no-summary", action="store_false", dest="summary", help="remove basecalling summary data (raw mode only)")
	parser.add_argument("--prefix", default=None, help="add prefix to output files to prevent overwrite")
	parser.add_argument("-t", "--threads", type=int, default=1, help="number of threads (default: 1)")
	parser.add_argument("-g", "--group", default="all", help="group number allows discrimination between different basecalling runs (default: all)")
	parser.add_argument("mode", choices=('lossless', 'deep-lossless', 'raw'), default='deep-lossless', help="choose compression mode (default: deep-lossless)")
	parser.add_argument("input", nargs="*", help="list of directories or fast5 files to shrink")
	args = parser.parse_args()
	
	args.test = checkTestMode(test, args)
	args.input = checkInputs(args)
	args.realtime = checkRealtime(args)
	
	return args
	
def checkSure():
	response = raw_input("Are you sure? (yes|no): ")
	if "yes".startswith(response):
		return 1
	else:
		return 0
