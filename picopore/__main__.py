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
from util import recursiveFindFast5, log, getPrefixedFilename
from compress import compressWrapper, chooseCompressFunc
from test import checkEquivalent
from os import remove

def run(revert, mode, input, y, threads, group, prefix):
	func = chooseCompressFunc(revert, mode)
	fileList = recursiveFindFast5(input)
	log("on {} files... ".format(len(fileList)))
	if args.y or checkSure():
		if args.threads <= 1:
			for f in fileList:
				compressWrapper([func,f, group, prefix])
		else:
			argList = [[func, f, group, prefix] for f in fileList]
			pool = Pool(threads)
			pool.map(compressWrapper, argList)
		log("Complete.")
		return 0
	else:
		log("User cancelled. Exiting.")
		return 1
	
def main():
	args = parseArgs()
	if args.test:
		result = 0
		fileList = recursiveFindFast5(input)
		run(False, args.mode, args.input, True, args.threads, args.group, args.prefix)
		run(True, args.mode, os.path.join(args.input, args.prefix), True, args.threads, args.group, None)
		for f in fileList:
			compressedFile = getPrefixedFilename(f)
			if not checkEquivalent(f, compressedFile):
				result = 1
			remove(compressedFile)
	else:
		result = run(args.revert, args.mode, args.input, args.y, args.threads, args.group, args.prefix)
	return result

if __name__ == "__main__":
	exit(main())
