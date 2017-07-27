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

from picopore.parse_args import parseArgs
from picopore.runner import *

def main():
    args = parseArgs()
    if args.test:
        runner = PicoporeTestRunner(args)
    elif args.realtime:
        runner = PicoporeRealtimeRunner(args)
    else:
        runner = PicoporeCompressionRunner(args)
    return runner.execute()

if __name__ == "__main__":
    exit(main())
