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

from __future__ import print_function
import os
import numpy as np
import glob

def log(message, end='\n'):
	print(message, end=end)
	
def getPrefixedFilename(filename, prefix=""):
	if prefix is None or prefix == "":
		return filename
	elif os.path.isdir(filename):
		return os.path.join(filename, prefix)
	else:
		return os.path.join(os.path.dirname(filename), ".".join([prefix, os.path.basename(filename)]))

def recursiveFindFast5(inp):
	files = []
	for path in inp:
		if os.path.isdir(path):
			files.extend(recursiveFindFast5([os.path.join(path, i) for i in os.listdir(path)]))
		elif os.path.isfile(path) and path.endswith(".fast5"):
			files.append(path)
		else:
			files.extend(glob.glob("{}*.fast5".format(path)))
	return files

def isType(obj, types):
	try:
		return type(obj).__name__ in types
	except TypeError as e:
		if str(e).endswith("is not iterable"):
			# got a single value, not a list
			return type(obj).__name__ == types
		else:
			raise e

def isGroup(obj):
	return isType(obj, ["Group"])
	
def isDataset(obj):
	return isType(obj, ["Dataset"])

def isInt(obj):
	return isType(obj, ['int', 'int4', 'int8', 'int16', 'int32', 'int64', 'uint', 'uint4', 'uint8', 'uint16', 'uint32', 'uint64'])

def isStr(obj):
	return isType(obj, ['str', 'string_', 'bytes_', 'unicode'])

def isArray(obj):
	return isType(obj, ['list', 'ndarray', 'MaskedArray'])

def isFloat(obj):
	return isType(obj, ['float', 'float16', 'float32', 'float64'])
	
def getUIntDtype(num):
	if num < 2**8:
		name='uint8'
	elif num < 2**16:
		name='uint16'
	elif num < 2**32:
		name='uint32'
	else:
		name='uint64'
	return name

def getIntDtype(num):
	if abs(num) < 2**7:
		name='int8'
	elif abs(num) < 2**15:
		name='int16'
	elif abs(num) < 2**31:
		name='int32'
	else:
		name='int64'
	return name
	
def getDtype(data):
	if isArray(data):
		if isInt(data[0]):
			if min(data) > 0:
				name=getUIntDtype(max(data))
			else:
				name=getIntDtype(max(data))
		elif isStr(data[0]):
			name='|S{}'.format(max(max([len(i) for i in data]),1))
		else:
			name=getDtype(data[0])
	elif isInt(data):
		if data > 0:
			name=getUIntDtype(data)
		else:
			name=getIntDtype(data)
	elif isStr(data):
		name='|S{}'.format(max(len(data),1))
	elif isFloat(data):
		# TODO: is there a better way to type floats? sig figs?
		name=type(data).__name__
	else:
		raise TypeError("Data type for value {} not recognised: {}".format(str(data), type(data).__name__))
		return None
	return np.dtype(name)

def recursiveFindDatasets(group, keyword):
	eventPaths = []
	if isGroup(group):
		for subgroup in group.values():
			eventPaths.extend(recursiveFindDatasets(subgroup, keyword))
	if keyword in group.name:
		eventPaths.append(group.name)
	return eventPaths

def findDatasets(f, group_id, keyword="Events", entry_point="Analyses"):
	eventPaths = []
	try:
		analyses = f.get(entry_point)
		for group in analyses.values():
			if group_id == "all" or group.endswith(group_id):
				eventPaths.extend(recursiveFindDatasets(group, keyword))
	except AttributeError:
		# no analyses, dont worry
		pass
	return eventPaths
	
def rewriteDataset(f, path, compression="gzip", compression_opts=1, dataset=None):
	obj = f.get(path)
	if not isDataset(obj):
		return
	attrs = obj.attrs
	dataset = obj.value if dataset is None else dataset
	del f[path]
	try:
		cols = dataset.dtype.names
		if cols is None:
			raise AttributeError("Array dtype is missing names")
		newtype=[(name, getDtype(dataset[name])) for name in dataset.dtype.names]
		f.create_dataset(path, data=dataset.astype(newtype), dtype=newtype, compression=compression, compression_opts=compression_opts)
	except AttributeError:
		try:
			f.create_dataset(path, data=dataset, dtype=getDtype(dataset), compression=compression, compression_opts=compression_opts)
		except TypeError as e:
			if str(e) == "Scalar datasets don't support chunk/filter options":
				f.create_dataset(path, data=dataset, dtype=getDtype(dataset))
			else:
				log(path)
				raise e
	for name, value in attrs.items():
		f[path].attrs[name] = value
		
def recursiveCollapseGroups(f, basegroup, path, group):
	for subname, object in group.items():
		subpath = "{}.{}".format(path, subname)
		if isGroup(object):
			recursiveCollapseGroups(f, basegroup, subpath, object)
		else:
			f.move(object.name, "{}/{}".format(basegroup, subpath))
	for k, v in group.attrs.items():
		f[basegroup].attrs.create("{}.{}".format(path, k), v, dtype=getDtype(v))
	del f[group.name]

def uncollapseGroups(f, basegroup):
	for name, object in basegroup.items():
		f.move("{}/{}".format(basegroup.name, name), name.replace(".", "/")) # TODO: does this include basegroup?
	for k, v in basegroup.attrs.items():
		k = k.split(".")
		groupname = "/".join(k[:-1])
		attrname = k[-1]
		try:
			f.create_group(groupname)
		except ValueError as e:
			if groupname in f:
				pass
			else:
				raise e
		f[groupname].attrs.create(attrname, v, dtype=getDtype(v))
	del f[basegroup.name]
