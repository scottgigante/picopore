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
import h5py
import os
from multiprocessing import Pool
from argparse import ArgumentParser
import subprocess
from numpy.lib.recfunctions import drop_fields, append_fields
import numpy as np

__basegroup_name__ = "Picopore"

def parseArgs(argv):
	parser = ArgumentParser(description="A tool for reducing the size of an Oxford Nanopore Technologies dataset without losing any data")
	parser.add_argument("command", choices=('shrink', 'unshrink'), help="Choose between shrinking and unshrinking files")
	parser.add_argument("-l", "--lossless", default=False, action="store_true", help="Shrinks files with no data loss")
	parser.add_argument("--raw", default=False, action="store_true", help="Reverts files to raw signal data only")
	parser.add_argument("-t", "--threads", type=int, default=1, help="number of threads")
	parser.add_argument("-g", "--group", default="all", help="Group number allows discrimination between different basecalling runs (default: all)")
	parser.add_argument("-y", action="store_true", default=False, help="Skip confirm step")
	parser.add_argument("input", nargs="*", help="List of directories or fast5 files to shrink")
	return parser.parse_args()

def isGroup(object):
	return type(group).__name__ == "Group"
	
def getIntDtype(num):
	if num < 2**4:
		name='int4'
	elif num < 2**8
		name='int8'
	elif num < 2**16:
		name='int16'
	elif num < 2**32:
		name='int32'
	else:
		name='int64'
	return np.dtype(name)
	
def getDtype(data):
	if type(data).__name__ in ['list', 'numpy.ndarray']:
		if type(data[0].__name__ == 'int'):
			return getIntDtype(max(data))
		elif type(data[0].__name__ == 'str'):
			return '|S{}'.format(max([len(i) for i in data]) + 1)
	if type(data).__name__ == 'int':
		return getIntDtype(data)
	elif type(data).__name__ == 'str':
		return '|S{}'.format(len(data))
	else:
		# TODO: float?
		return None

def recursiveFindEvents(group):
	eventPaths = []
	if isGroup(group):
		for subgroup in group.values():
			eventPaths.extend(recursiveFindEvents(subgroup))
	elif group.name.endswith("Events") or group.name.endswith("Alignment"):
		eventPaths.append(group.name)
	return eventPaths

def findEvents(f, group_id):
	eventPaths = []
	analyses = f.get("Analyses")
	for group in analyses.values():
		if group_id == "all" or group.endswith(group_id):
			eventPaths.extend(recursiveFindEvents(group))
	return eventPaths	
	
def rewriteDataset(f, path, compression="gzip", compression_opts=1):
	attrs = f.get(path).attrs
	dataset = f.get(path).value
	del f[path]
	f.create_dataset(path, data=dataset, dtype=dataset.dtype, compression=compression, compression_opts=compression_opts)
	for name, value in attrs.items():
		f[path].attrs[name] = value
		
def recursiveCollapseGroups(f, basegroup, path, group):
	for subname, object in group:
		subpath = "{}\/{}".format(path, subname)
		if isGroup(object):
			recursiveCollapseGroups(f, basegroup, subpath, object)
		else:
			f.move(object.name, "{}/{}".format(basename, subpath))
		for k, v in group.attrs.items():
			basegroup.attrs.create("{}\/{}".format(subpath, k), v, dtype=getMinDtype(v))

def uncollapseGroups(f, basegroup):
	for name, object in basegroup.items():
		f.move(name, name.replace("\/", "/")) # TODO: does this include basegroup?
	for k, v in basegroup.attrs.items():
		k = k.split("\/")
		groupname = "/".join(k[:-1])
		attrname = k[-1]
		f.create_group(groupname)
		f[groupname].attrs.create(attrname, v, dtype=getMinDtype(v))

def deepLosslessCompress(f, group):
	paths = findEvents(f, group)
	eventDetectionPaths = [path for path in paths if "EventDetection" in path]
	# TODO: what happens if there are multiple event detections? Is this even possible?
	if len(eventDetectionPaths > 1):
		print("Multiple event detections detected. Performing regular lossless compression.")
	elif len(eventDetectionPaths == 0):
		# no eventdetection to align to, just do lossless compression
		print("No event detection detected. Performing regular lossless decompression.")
	else:
		# index event detection
		eventDetectionPath = eventDetectionPaths[0]
		sampleRate = f["UniqueGlobalKey/channel_id"]["sampling_rate"]
		paths.remove(eventDetectionPath)
		for path in paths:
			if path.endswith("Events"):
				# index back to event detection
				dataset = f[path].value
				start = int(round(sampleRate * dataset["start"][0]))
				end = int(round(sampleRate * dataset["start"][-1] + 1)) # TODO: round properly
				assert(end - start == dataset.shape[0]) # hopefully!
				# otherwise, event by event
				drop_fields(dataset, ["mean", "stdv", "start", "length"])
				append_fields(dataset, ["start"], [range(start, end)], [getDtype(end)])
		# remove group hierarchy
		f.create_group(__basegroup_name__)
		for name, group in f.items():
			if name != __basegroup_name__:
				recursiveCollapseGroups(f, __basegroup_name__, name, object)
	return losslessCompress(f, group)

def deepLosslessDecompress(f, group):
	paths = findEvents(f, group)
	eventDetectionPaths = [path for path in paths if "EventDetection" in path]
	# TODO: what happens if there are multiple event detections? Is this even possible?
	if len(eventDetectionPaths > 1):
		print("Multiple event detections detected. Performing regular lossless decompression.")
	elif len(eventDetectionPaths == 0):
		# no eventdetection to align to, just do lossless compression
		print("No event detection detected. Performing regular lossless decompression.")
	else:
		eventDetectionPath = eventDetectionPaths[0]
		sampleRate = f["UniqueGlobalKey/channel_id"]["sampling_rate"]
		paths.remove(eventDetectionPath)
		for path in paths:
			if path.endswith("Events"):
				# index back to event detection
				dataset = f[path].value
				if "mean" not in dataset.dtype.names:
					start = dataset["start"][0]
					end = dataset["start"][-1] + 1
					assert(end - start == dataset.shape[0]) # hopefully!
					# otherwise, event by event
					eventData = f[eventDetectionPath].value[start:end]
					drop_fields(dataset, "start")
					start = [i/sampleRate for i in eventData["start"]]
					append_fields(dataset, ["mean", "start", "stdv", "length"], [eventData["mean"], start, eventData["stdv"], eventData["length"])	
		# rebuild group hierarchy
		if __basegroup_name__ in f.keys():
			uncollapseGroups(f, f[__basegroup_name__])
	return losslessDecompress(f, group)

def losslessCompress(f, group):
	for path in findEvents(f, group):
		rewriteDataset(f, path, "gzip", 9)
	return "GZIP=9"
		
def losslessDecompress(f, group):
	for path in findEvents(f, group):
		rewriteDataset(f, path)
	return "GZIP=1"
		
def rawCompress(f, group):
	for path in findEvents(f, group):
		del f[path]
	return "GZIP=9"

def compress(func, filename, group):
	with h5py.File(filename, 'r+') as f:
		filtr = func(f, group)
	subprocess.call(["h5repack","-f",filtr,filename,"{}.tmp".format(filename)])
	subprocess.Popen(["mv","{}.tmp".format(filename),filename])

def compressWrapper(args):
	return compress(*args)
		
def chooseShrinkFunc(args):
	if args.command == "shrink":
		if args.lossless:
			func = losslessCompress
			name = "Performing lossless compression "
		elif args.raw:
			func = rawCompress
			name = "Reverting to raw signal "
	else:
		if args.lossless:
			func = losslessDecompress
			name = "Performing lossless decompression "
	try:
		print(name, end='')
	except NameError:
		print("No shrinking method selected")
		exit()
	return func
		
def recursiveFindFast5(input):
	files = []
	for path in input:
		if os.path.isdir(path):
			files.extend(recursiveFindFast5(os.listdir(path)))
		elif os.path.isfile(path) and path.endswith(".fast5"):
			files.append(path)
	return files
	
def checkSure():
	response = raw_input("Are you sure? (yes|no): ")
	if "yes".startswith(response):
		return 1
	else:
		return 0
	
def main():
	args = parseArgs(argv)
	func = chooseShrinkFunc(args)
	fileList = recursiveFindFast5(args.input)
	print("on {} files... ".format(len(fileList)))
	if args.y or checkSure():
		if args.threads <= 1:
			[compress(func,f, args.group) for f in fileList]
		else:
			argList = [[func, f, args.group] for f in fileList]
			pool = Pool(args.threads)
			pool.map(compressWrapper, argList)
		print("Complete.")
	else:
		print("User cancelled. Exiting.")

if __name__ == "__main__":
	main()
