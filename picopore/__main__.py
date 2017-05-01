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
from time import sleep

from picopore.parse_args import parseArgs, checkSure
from picopore.util import recursiveFindFast5, log, getPrefixedFilename
from picopore.compress import compress, chooseCompressFunc
from picopore.test import checkEquivalent
from picopore.multiprocess import Multiprocessor

def run(revert, mode, inp, y=False, threads=1, group="all", prefix=None, fastq=True, summary=False, print_every=100, skip_root=False, multiprocessor=None):
    func, message = chooseCompressFunc(revert, mode, fastq, summary)
    fileList = recursiveFindFast5(inp, skip_root)
    if len(fileList) == 0:
        log("No files found under {}".format(inp))
        return 0
    preSize = sum([os.path.getsize(f) for f in fileList])
    postSize = 0
    log("{} on {} files... ".format(message, len(fileList)))
    if y or checkSure():
        if threads <= 1 and multiprocessor is None:
            for f in fileList:
                postSize += compress(func,f, group, prefix, print_every)
        else:
            argList = [[func, f, group, prefix, print_every] for f in fileList]
            if multiprocessor is None:
                multiprocessor = Multiprocessor(threads)
            multiprocessor.apply_async(compress, argList)
            postSize = multiprocessor.join()
        if revert:
            preStr, postStr = "Compressed size:", "Reverted size:"
        else:
            preStr, postStr = "Original size:", "Compressed size:"
        log("Complete.")

        str_len = max(len(preStr), len(postStr)) + 1
        num_len = len(str(max(preSize, postSize)))
        log("{}{}".format(preStr.ljust(str_len), str(preSize).rjust(num_len)))
        log("{}{}".format(postStr.ljust(str_len), str(postSize).rjust(num_len)))
        return preSize
    else:
        log("User cancelled. Exiting.")
        exit(1)

def runTest(args):
    fileList = recursiveFindFast5(args.input, args.skip_root)
    try:
        run(False, args.mode, fileList, True, args.threads, args.group, args.prefix, args.fastq, args.summary, args.print_every)
        run(True, args.mode, [getPrefixedFilename(f, args.prefix) for f in fileList], True, args.threads, args.group, None, args.fastq, args.summary, args.print_every)
        for f in fileList:
            compressedFile = getPrefixedFilename(f, args.prefix)
            exitcode = checkEquivalent(f, compressedFile)
    finally:
        for f in fileList:
            try:
                os.remove(getPrefixedFilename(f, args.prefix))
            except OSError:
                # file never created
                pass
    return exitcode

def runRealtime(args):
    from picopore.realtime import ReadsFolder
    readsFolder = ReadsFolder(args)
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        log("\nExiting Picopore.")
    readsFolder.stop()
    return 0

def main():
    args = parseArgs()
    if args.test:
        exitcode = runTest(args)
    elif args.realtime:
        exitcode = runRealtime(args)
    else:
        exitcode = run(args.revert, args.mode, args.input, args.y, args.threads, args.group, args.prefix, args.fastq, args.summary, args.print_every, args.skip_root)
    return exitcode

if __name__ == "__main__":
    exit(main())
