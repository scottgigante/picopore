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
from __main__ import run

class ReadsFolder:
	def __init__(self, args):
		self.args = args
		self.observer = Observer()
		observedPaths = []
		for path in args.input:
			if os.path.isdir(path):
				observer.schedule(event_handler, path, recursive=True)
				observedPaths.append(path)
		if self.args.prefix is not None:
			ignore_patterns = ["{}*.fast5".format(self.args.prefix)]
		else:
			ignore_patterns = []
		self.event_handler = watchdog.events.PatternMatchingEventHandler(patterns=["*.fast5"],
									ignore_patterns=ignore_patterns,
									ignore_directories=True)
		self.event_handler.on_created = self.on_created
		log("Monitoring {} in real time. Press Ctrl+C to exit.".format(", ".join(self.args.input)))
		self.observer.start()
		run(args.revert, args.mode, args.input, args.y, args.threads, args.group, args.prefix)

    def on_created(self, event):
        run(self.args.revert, self.args.mode, [event.src_path], self.args.y, self.args.threads, self.args.group, self.args.prefix)

    def stop(self):
        self.observer.stop()
        self.observer.join()