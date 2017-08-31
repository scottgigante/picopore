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

import re
import functools
import h5py

from picopore.parse_args import parseRenameArgs
from picopore.runner import AbstractPicoporeRunner
from picopore.util import findDatasets, log

def rename(filename, pattern, replacement):
    try:
        with h5py.File(filename, 'r+') as f:
            for path in findDatasets(f, entry_point="/", keyword=pattern, match_child=True):
                newPath = re.sub(pattern, replacement, path)
                f[newPath] = f[path]
                del f[path]
                log("Renamed {} to {}".format(path, newPath))
        return 0
    except Exception as e:
        log("ERROR: " + str(e))
        return 1

class PicoporeRenameRunner(AbstractPicoporeRunner):

    def __init__(self, args):
        super(PicoporeRenameRunner, self).__init__(args)
        self.pattern = args.pattern
        self.replacement = args.replacement
        self.processed = 0

    def get_func(self):
        func = functools.partial(rename, pattern=self.pattern, replacement=self.replacement)
        message = "Renaming {} to {}".format(self.pattern, self.replacement)
        return func, message

    def preprocess(self, fileList):
        self.processed += len(fileList)

    def postprocess(self, results):
        log("Successfully renamed {} of {} files.".format(self.processed - sum(results), self.processed))
        return self.processed

__description = """"A tool for renaming groups and datasets within Oxford Nanopore Technologies FAST5 files"""
        
def main():
    args = parseRenameArgs(description=__description)
    runner = PicoporeRenameRunner(args)
    return runner.execute()

if __name__ == "__main__":
    exit(main())
