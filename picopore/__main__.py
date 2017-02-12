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

from multiprocessing import Pool

from parse_args import parseArgs, checkSure
from util import recursiveFindFast5, log
from compress import compressWrapper, chooseCompressFunc
	
def main():
	args = parseArgs()
	func = chooseCompressFunc(args)
	fileList = recursiveFindFast5(args.input)
	log("on {} files... ".format(len(fileList)))
	if args.y or checkSure():
		if args.threads <= 1:
			[compressWrapper([func,f, args.group, args.prefix]) for f in fileList]
		else:
			argList = [[func, f, args.group, args.prefix] for f in fileList]
			pool = Pool(args.threads)
			pool.map(compressWrapper, argList)
		log("Complete.")
		return 0
	else:
		log("User cancelled. Exiting.")
		return 1

if __name__ == "__main__":
	exit(main())
