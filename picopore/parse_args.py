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
from version import __version__

def parseArgs():
	parser = ArgumentParser(description="A tool for reducing the size of an Oxford Nanopore Technologies dataset without losing any data")#, usage='''picopore [-h] [-v] [-y] [-l] [--raw] [-t THREADS] [-g GROUP]
#	{shrink,unshrink} /path/to/fast5''')
	parser.add_argument('-v', '--version', action='version', version='Picopore {}'.format(__version__))
	parser.add_argument("-y", action="store_true", default=False, help="skip confirm step")
	parser.add_argument("--revert", default=False, action="store_true", help="reverts files to original size (lossless modes only)")
	parser.add_argument("-t", "--threads", type=int, default=1, help="number of threads (default: 1)")
	parser.add_argument("-g", "--group", default="all", help="group number allows discrimination between different basecalling runs (default: all)")
	parser.add_argument("--prefix", default=None, help="add prefix to output files to prevent overwrite")
	parser.add_argument("mode", choices=('lossless', 'deep-lossless', 'raw'), default='deep-lossless', help="choose compression mode (default: deep-lossless)")
	parser.add_argument("input", nargs="*", help="list of directories or fast5 files to shrink")
	return parser.parse_args()
	
def checkSure():
	response = raw_input("Are you sure? (yes|no): ")
	if "yes".startswith(response):
		return 1
	else:
		return 0
