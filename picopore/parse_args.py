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

from argparse import ArgumentParser

def parseArgs():
	parser = ArgumentParser(description="A tool for reducing the size of an Oxford Nanopore Technologies dataset without losing any data")
	parser.add_argument("command", choices=('shrink', 'unshrink'), help="Choose between shrinking and unshrinking files")
	parser.add_argument("-l", "--lossless", default=False, action="store_true", help="Shrinks files with no data loss")
	parser.add_argument("--raw", default=False, action="store_true", help="Reverts files to raw signal data only")
	parser.add_argument("-t", "--threads", type=int, default=1, help="number of threads")
	parser.add_argument("-g", "--group", default="all", help="Group number allows discrimination between different basecalling runs (default: all)")
	parser.add_argument("-y", action="store_true", default=False, help="Skip confirm step")
	parser.add_argument("input", nargs="*", help="List of directories or fast5 files to shrink")
	return parser.parse_args()
	
def checkSure():
	response = raw_input("Are you sure? (yes|no): ")
	if "yes".startswith(response):
		return 1
	else:
		return 0
