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

import h5py
from picopore.util import log, isGroup, isArray

def checkContents(obj1, obj2, name=None):
    name = obj1.name if name is None else name
    keys1 = obj1.keys()
    keys2 = obj2.keys()
    exitcode = 0
    for key in keys1:
        if key not in keys2:
            log("Failure: {} missing from file 2".format("/".join([obj2.name, key])))
            exitcode += 1
    for key in keys2:
        if key not in keys1:
            log("Failure: {} missing from file 1".format("/".join([obj1.name, key])))
            exitcode += 1
    return exitcode

def checkData(data1, data2, name):
    match = data1==data2
    exitcode = 0
    if isArray(match):
        match = (data1==data2).all()
    if not match:
        positions = [i for i in range(len(data1)) if not data1[i] == data2]
        for pos in positions:
            log("Failure: {}[{}] - file1={}, file2={}".format(name, pos, data1[pos], data2[pos]))
            exitcode += 1
    return exitcode

def recursiveCheckEquivalent(file1, file2, name):
    obj1 = file1[name]
    obj2 = file1[name]
    # check attributes
    attr1 = obj1.attrs
    attr2 = obj2.attrs
    attrsName = "/".join([name, "attrs"])
    exitcode = checkContents(attr1, attr2, attrsName)
    for key, value in attr1.items():
        try:
            if not attr2[key] == value:
                log("Failure: {} - file1={}, file2={}".format("/".join([attrsName, key]), value, attr2[key]))
                exitcode += 1
        except ValueError as e:
            # probably a numpy array
            if str(e) == "The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()" and not (attr2[key] == value).all():
                log("Failure: {} - file1={}, file2={}".format("/".join([attrsName, key]), value, attr2[key]))
                exitcode += 1
    # check subgroups / datasets
    if isGroup(obj1):
        exitcode += checkContents(obj1, obj2)
        for key in obj1.keys():
            exitcode += recursiveCheckEquivalent(file1, file2, "/".join([name, key]))
    else:
        if not obj1.shape == obj2.shape:
            log("Failure: {}.shape - file1={}, file2={}".format(name, obj1.shape, obj2.shape))
        if obj1.dtype.names is None:
            # just one column
            exitcode += checkData(obj1, obj2, name)
        else:
            for col in obj1.dtype.names:
                exitcode += checkData(obj1[col], obj2[col], ".".join([name, col]))
    return exitcode

def checkEquivalent(fn1, fn2):
    log("Checking equivalence of {} (file 1) and {} (file 2)...".format(fn1, fn2))
    with h5py.File(fn1, 'r') as file1, h5py.File(fn2, 'r') as file2:
        exitcode = checkContents(file1, file2)
        for group in file1.values():
            exitcode += recursiveCheckEquivalent(file1, file2, group.name)
    log("Complete with {} errors.".format(exitcode))
    return exitcode
