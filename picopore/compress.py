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
import subprocess
import numpy as np
import h5py
from numpy.lib.recfunctions import drop_fields, append_fields

from util import log, isGroup, getDtype, findEvents, rewriteDataset, recursiveCollapseGroups, uncollapseGroups

def chooseCompressFunc(args):
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
		log(name, end='')
	except NameError:
		log("No shrinking method selected")
		exit()
	return func

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
					append_fields(dataset, ["mean", "start", "stdv", "length"], [eventData["mean"], start, eventData["stdv"], eventData["length"]])	
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
