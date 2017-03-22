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
	for key in keys1:
		if key not in keys2:
			log("Failure: {} missing from file 2".format("/".join([obj2.name, key])))
	for key in keys2:
		if key not in keys1:
			log("Failure: {} missing from file 1".format("/".join([obj1.name, key])))
			
def checkData(data1, data2, name):
	match = data1==data2
	if isArray(match):
		match = (data1==data2).all()
	if not match:
		positions = [i for i in range(len(data1)) if not data1[i] == data2]
		for pos in positions:
			log("Failure: {}[{}] - file1={}, file2={}".format(name, pos, data1[pos], data2[pos]))

def recursiveCheckEquivalent(file1, file2, name):
	obj1 = file1[name]
	obj2 = file1[name]
	# check attributes
	attr1 = obj1.attrs
	attr2 = obj2.attrs
	attrsName = "/".join([name, "attrs"])
	checkContents(attr1, attr2, attrsName)
	for key, value in attr1.items():
		try:
			if not attr2[key] == value:
				log("Failure: {} - file1={}, file2={}".format("/".join([attrsName, key]), value, attr2[key]))
		except ValueError as e:
			# probably a numpy array
			if str(e) == "The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()" and not (attr2[key] == value).all():
				log("Failure: {} - file1={}, file2={}".format("/".join([attrsName, key]), value, attr2[key]))
	# check subgroups / datasets
	if isGroup(obj1):
		checkContents(obj1, obj2)
		for key in obj1.keys():
			recursiveCheckEquivalent(file1, file2, "/".join([name, key]))
	else:
		if not obj1.shape == obj2.shape:
			log("Failure: {}.shape - file1={}, file2={}".format(name, obj1.shape, obj2.shape))
		if obj1.dtype.names is None:
			# just one column
			checkData(obj1, obj2, name)
		else:
			for col in obj1.dtype.names:
				checkData(obj1[col], obj2[col], ".".join([name, col]))

def checkEquivalent(fn1, fn2):
	log("Checking equivalence of {} (file 1) and {} (file 2)...".format(fn1, fn2))
	with h5py.File(fn1, 'r') as file1, h5py.File(fn2, 'r') as file2:
		checkContents(file1, file2)
		for group in file1.values():
			recursiveCheckEquivalent(file1, file2, group.name)
	log("Complete.")
