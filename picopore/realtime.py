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

from picopore.multiprocess import Multiprocessor
from picopore.runner import PicoporeCompressionRunner
from picopore.compress import chooseCompressFunc
from picopore.parse_args import parseArgs
from picopore.util import log

class ReadsFolder(object):
    def __init__(self, runner):
        self.runner = runner

        self.event_handler = PatternMatchingEventHandler(patterns=["*.fast5"],
                ignore_patterns=[],
                ignore_directories=True)
        self.event_handler.on_created = self.on_created
        self.event_handler.on_moved = self.on_moved

        self.observer = Observer()

        self.observedPaths = []
        for path in self.runner.input:
            if os.path.isdir(path):
                self.observer.schedule(self.event_handler, path, recursive=True)
                self.observedPaths.append(path)
        log("Monitoring {} in real time. Press Ctrl+C to exit.".format(", ".join(self.observedPaths)))

    def start(self):
        self.observer.start()
        self.runner.run(postprocess=False)

    def add_file(self, path):
        self.runner.process([path])

    def on_created(self, event):
        if self.runner.skip_root and os.path.dirname(event.src_path) in self.observedPaths:
            return 0
        elif self.runner.prefix is not None and os.path.basename(event.src_path).startswith(self.runner.prefix):
            return 0
        else:
            self.add_file(event.src_path)
            return 0

    def on_moved(self, event):
        if self.runner.skip_root and os.path.dirname(event.src_path) in self.observedPaths and os.path.dirname(event.dest_path) not in self.observedPaths:
            self.add_file(event.dest_path)

    def stop(self):
        log("Processing in-progress files. Press Ctrl-C again to abort.")
        try:
            self.runner.stop()
        except KeyboardInterrupt:
            log("Aborted.")
            pass

        self.observer.stop()
        self.observer.join()

class PicoporeRealtimeRunner(PicoporeCompressionRunner):

    def __init__(self, args):
        super(PicoporeRealtimeRunner, self).__init__(args)
        _, name = chooseCompressFunc(self.revert, self.mode, self.fastq, self.summary, self.manual, realtime=True)
        log(name + "...",end='')
        if self.y:
            print()
        elif checkSure():
            self.y = True
        else:
            exit(1)
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

__description = """"picopore-realtime monitors a directory for new reads and compresses them in real time"""

def main():
    args = parseArgs(description=__description, prog='picopore-realtime')
    runner = PicoporeRealtimeRunner(args)
    return runner.execute()

if __name__ == "__main__":
    exit(main())
