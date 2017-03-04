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
from picopore.util import log

class ReadsFolder():
	def __init__(self, args):
		self.args = args
		self.event_handler = PatternMatchingEventHandler(patterns=["*.fast5"],
				ignore_patterns=[],
				ignore_directories=True)
		self.event_handler.on_created = self.on_created
		self.observer = Observer()
		observedPaths = []
		for path in args.input:
			if os.path.isdir(path):
				self.observer.schedule(self.event_handler, path, recursive=True)
				observedPaths.append(path)
		log("Monitoring {} in real time. Press Ctrl+C to exit.".format(", ".join(self.args.input)))
		self.observer.start()
		run(args.revert, args.mode, args.input, args.y, args.threads, args.group, args.prefix, args.fastq, args.summary)

	def on_created(self, event):
		if self.args.prefix is None or not os.path.basename(event.src_path).startswith(self.args.prefix):
			run(self.args.revert, self.args.mode, [event.src_path], self.args.y, self.args.threads, self.args.group, self.args.prefix, self.args.fastq, self.args.summary)

	def stop(self):
		self.observer.stop()
		self.observer.join()
