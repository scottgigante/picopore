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

# Original code at https://github.com/jreese/multiprocessing-keyboardinterrupt
# Copyright (c) 2011 John Reese
# Licensed under the MIT License

import multiprocessing
import signal

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

class Multiprocessor:

    def __init__(self, threads):
        self.pool = self.init_pool(threads)
        self.results = []

    def init_pool(self, threads):
        return multiprocessing.Pool(threads, init_worker)

    def apply_async(self, func, argList):
        for arg in argList:
            self.results.append(self.pool.apply_async(func, args=[arg]))

    def join(self):
        try:
            return [r.get() for r in self.results]

        except KeyboardInterrupt:
            self.pool.terminate()
            self.pool.join()
            raise

    def wait(self):
        try:
            for r in self.results:
                r.wait()
            return 0

        except KeyboardInterrupt:
            self.pool.terminate()
            self.pool.join()
            raise

    def __del__(self):
        self.pool.close()
        self.pool.join()
