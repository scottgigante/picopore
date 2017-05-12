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
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from picopore.__main__ import run
from picopore.util import log, getPrefixedFilename
from picopore.multiprocess import Multiprocessor
from picopore.compress import chooseCompressFunc

class ReadsFolder():
    def __init__(self, args):
        self.args = args

        self.event_handler = PatternMatchingEventHandler(patterns=["*.fast5"],
                ignore_patterns=[],
                ignore_directories=True)
        self.event_handler.on_created = self.on_created
        self.event_handler.on_moved = self.on_moved

        self.observer = Observer()
        self.multiprocessor = Multiprocessor(args.threads)
        self.compress, self.message = chooseCompressFunc(args.revert, args.mode, args.fastq, args.summary, args.manual)
        self.preSize = 0

        self.observedPaths = []
        for path in args.input:
            if os.path.isdir(path):
                self.observer.schedule(self.event_handler, path, recursive=True)
                self.observedPaths.append(path)
        log("Monitoring {} in real time. Press Ctrl+C to exit.".format(", ".join(self.args.input)))
        self.observer.start()
        self.preSize += run(args.revert, args.mode, args.input, args.y, args.threads, args.group, args.prefix, args.fastq, args.summary, args.manual, args.print_every, args.skip_root, self.multiprocessor)

    def add_file(self, path):
        self.preSize += os.path.getsize(path)
        argList = [[path, self.args.group, self.args.prefix, self.args.print_every]]
        self.multiprocessor.apply_async(self.compress, argList)

    def on_created(self, event):
        if self.args.skip_root and os.path.dirname(event.src_path) in self.observedPaths:
            return 0
        elif self.args.prefix is not None and os.path.basename(event.src_path).startswith(self.args.prefix):
            return 0
        else:
            self.add_file(event.src_path)
            return 0

    def on_moved(self, event):
        if self.args.skip_root and os.path.dirname(event.src_path) in self.observedPaths and os.path.dirname(event.dest_path) not in self.observedPaths:
            self.add_file(event.dest_path)

    def stop(self):
        log("Processing in-progress files. Press Ctrl-C again to abort.")
        try:
            postSize = self.multiprocessor.join()
            log("Complete.")
            if self.args.revert:
                preStr, postStr = "Compressed size:", "Reverted size:"
            else:
                preStr, postStr = "Original size:", "Compressed size:"
            str_len = max(len(preStr), len(postStr)) + 1
            num_len = len(str(max(self.preSize, postSize)))
            log("{}{}".format(preStr.ljust(str_len), str(self.preSize).rjust(num_len)))
            log("{}{}".format(postStr.ljust(str_len), str(postSize).rjust(num_len)))
        except KeyboardInterrupt:
            log("Aborted.")
            pass

        self.observer.stop()
        self.observer.join()
