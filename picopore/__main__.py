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
import os
import sys
from time import sleep

from picopore.parse_args import parseArgs, checkSure
from picopore.util import recursiveFindFast5, log, getPrefixedFilename
from picopore.compress import compressWrapper, chooseCompressFunc
from picopore.test import checkEquivalent

def run(revert, mode, inp, y=False, threads=1, group="all", prefix=None, fastq=True, summary=False):
	func, message = chooseCompressFunc(revert, mode, fastq, summary)
	fileList = recursiveFindFast5(inp)
	if len(fileList) == 0:
		log("No files found under {}".format(inp))
		return 0
	preSize = sum([os.path.getsize(f) for f in fileList])
	log("{} on {} files... ".format(message, len(fileList)))
	if y or checkSure():
		if threads <= 1:
			for f in fileList:
				compressWrapper([func,f, group, prefix])
		else:
			argList = [[func, f, group, prefix] for f in fileList]
			pool = Pool(threads)
			pool.map(compressWrapper, argList)
		if revert:
			preStr, postStr = "Compressed size:", "Reverted size:"
		else:
			preStr, postStr = "Original size:", "Compressed size:"
		log("Complete.")
		postSize = sum([os.path.getsize(getPrefixedFilename(f, prefix)) for f in fileList])
		str_len = max(len(preStr), len(postStr)) + 1
		num_len = len(str(max(preSize, postSize)))
		log("{}{}".format(preStr.ljust(str_len), str(preSize).rjust(num_len)))
		log("{}{}".format(postStr.ljust(str_len), str(postSize).rjust(num_len)))
		return 0
	else:
		log("User cancelled. Exiting.")
		exit(1)
		
def runTest(args):
	fileList = recursiveFindFast5(args.input)
	try:
		run(False, args.mode, args.input, True, args.threads, args.group, args.prefix, args.fastq, args.summary)
		run(True, args.mode, [os.path.join(os.path.dirname(i), getPrefixedFilename(i, args.prefix)) for i in args.input], True, args.threads, args.group, None, args.fastq, args.summary)
		for f in fileList:
			compressedFile = getPrefixedFilename(f, args.prefix)
			checkEquivalent(f, compressedFile)
	finally:
		for f in fileList:
			try:
				os.remove(getPrefixedFilename(f, args.prefix))
			except OSError:
				# file never created
				pass
	return 0

def runRealtime(args):
	from picopore.realtime import ReadsFolder
	readsFolder = ReadsFolder(args)
	try:
		while True:
			sleep(1)
	except KeyboardInterrupt:
		log("\nExiting Picopore.")
	readsFolder.stop()
	
def main():
	args = parseArgs()
	if args.test:
		runTest(args)
	elif args.realtime:
		runRealtime(args)
	else:
		run(args.revert, args.mode, args.input, args.y, args.threads, args.group, args.prefix, args.fastq, args.summary)
	return 0

if __name__ == "__main__":
	exit(main())
