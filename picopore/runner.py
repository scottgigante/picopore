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
import functools
from shutil import copyfile
import numpy as np

from picopore.parse_args import checkSure
from picopore.util import recursiveFindFast5, log, getPrefixedFilename
from picopore.compress import chooseCompressFunc
from picopore.test import checkEquivalent
from picopore.multiprocess import Multiprocessor
from picopore.realtime import ReadsFolder

def _process_func(filename, func, prefix, print_every):
        if prefix is not None:
            newFilename = getPrefixedFilename(filename, prefix)
            copyfile(filename, newFilename)
        else:
            newFilename = filename
        result = func(newFilename)
        if result is not None and print_every > 0 and np.random.rand() < 1.0/print_every:
            log('.', end='')
        return result

class AbstractPicoporeRunner(object):

    def __init__(self, args):
        self.y = args.y
        self.multiprocessor = Multiprocessor(args.threads)
        self.prefix = args.prefix
        self.skip_root = args.skip_root
        self.print_every = args.print_every
        self.input = args.input

    def get_func(self):
        raise NotImplementedError()
        return func, message

    def preprocess(self, fileList):
        raise NotImplementedError()

    def postprocess(self, results):
        raise NotImplementedError()
        return 0 # exitcode

    def getFileList(self):
        return recursiveFindFast5(self.input, self.skip_root)

    def process(self, fileList):
        self.preprocess(fileList)
        self.multiprocessor.apply_async(self.func, fileList)

    def stop(self):
        results = self.multiprocessor.join()
        log("Complete.")
        return self.postprocess(results)

    def run(self, postprocess=True):
        func, message = self.get_func()
        self.func = functools.partial(_process_func, func=func, prefix=self.prefix, print_every=self.print_every)
        fileList = self.getFileList()
        if len(fileList) == 0:
            return 0
        log("{} on {} files... ".format(message, len(fileList)))
        if self.y or checkSure():
            self.process(fileList)
            if postprocess:
                return self.stop()
            else:
                return self.multiprocessor.wait()
        else:
            log("User cancelled. Exiting.")
            exit(1)

    def execute(self):
        self.run()
        return 0

class PicoporeCompressionRunner(AbstractPicoporeRunner):

    def __init__(self, args):
        super(PicoporeCompressionRunner, self).__init__(args)
        self.mode = args.mode
        self.revert = args.revert
        self.fastq = args.fastq
        self.summary = args.summary
        self.manual = args.manual
        self.group = args.group
        self.preSize = 0
        self.postSize = 0

    def get_func(self):
        func, message = chooseCompressFunc(self.revert, self.mode, self.fastq, self.summary, self.manual)
        func = functools.partial(func, group=self.group)
        return func, message

    def preprocess(self, fileList):
        self.preSize += sum([os.path.getsize(f) for f in fileList])

    def postprocess(self, results):
        self.postSize = sum(results)
        if self.revert:
            preStr, postStr = "Compressed size:", "Reverted size:"
        else:
            preStr, postStr = "Original size:", "Compressed size:"
        str_len = max(len(preStr), len(postStr)) + 1
        num_len = len(str(max(self.preSize, self.postSize)))
        log("{}{}".format(preStr.ljust(str_len), str(self.preSize).rjust(num_len)))
        log("{}{}".format(postStr.ljust(str_len), str(self.postSize).rjust(num_len)))
        return self.preSize

class PicoporeTestRunner(PicoporeCompressionRunner):

    def __init__(self, args):
        super(PicoporeTestRunner, self).__init__(args)
        self.fileList = super(PicoporeTestRunner, self).getFileList()
        self.y = True
        self.originalFileList = self.fileList

    def getFileList(self):
        return self.fileList

    def getReversionFileList(self):
        return [getPrefixedFilename(f, self.prefix) for f in self.fileList]

    def execute(self):
        exitcode=1
        if len(self.fileList) == 0:
            return 0
        try:
            self.revert = False
            self.run()

            self.preSize = 0
            self.postSize = 0
            self.revert = True
            self.fileList = self.getReversionFileList()
            self.prefix = None
            self.run()
            exitcode = 0
            for i in range(len(self.fileList)):
                exitcode += checkEquivalent(self.originalFileList[i], self.fileList[i])
        except Exception as e:
            log("ERROR: " + str(e))
        finally:
            for f in self.fileList:
                try:
                    os.remove(f)
                except OSError:
                    # file never created
                    pass
        return exitcode

class PicoporeRealtimeRunner(PicoporeCompressionRunner):

    def __init__(self, args):
        super(PicoporeRealtimeRunner, self).__init__(args)
        self.readsFolder = ReadsFolder(self)

    def execute(self):
        self.readsFolder.start()
        try:
            while True:
                sleep(5)
        except KeyboardInterrupt:
            log("\nExiting Picopore.")
        self.readsFolder.stop()
        return 0
