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
import os
from numpy.lib.recfunctions import drop_fields, append_fields
from shutil import copyfile

from picopore.util import log, isGroup, getDtype, findDatasets, rewriteDataset, recursiveCollapseGroups, uncollapseGroups, getPrefixedFilename

__basegroup_name__ = "Picopore"
__raw_compress_keywords__ = ["Alignment","Log","Configuration","HairpinAlign","Calibration_Strand","Hairpin_Split","EventDetection","Events"]

def chooseCompressFunc(revert, mode, fastq, summary):
	if revert:
		if mode == 'lossless':
			func = losslessDecompress
			name = "Performing lossless decompression"
		elif mode == 'deep-lossless':
			func = deepLosslessDecompress
			name = "Performing deep lossless decompression"
		else:
			log("Unable to revert raw files. Please use a basecaller instead.")
			exit(1)
	else:
		if mode == 'lossless':
			func = losslessCompress
			name = "Performing lossless compression"
		elif mode == 'deep-lossless':
			func = deepLosslessCompress
			name = "Performing deep lossless compression"
		elif mode == 'raw':
			if fastq and summary:
				func = rawCompressFastqSummary
				name = "Performing raw compression with FASTQ and summary"
			elif fastq:
				func = rawCompressFastqNoSummary
				name = "Performing raw compression with FASTQ and no summary"
			elif summary:
				func = rawCompressSummaryNoFastq
				name = "Performing raw compression with summary and no FASTQ"
			else:
				func = rawCompressMinimal
				name = "Performing raw compression with no summary and no FASTQ"
	try:
		return func, name
	except NameError:
		log("No compression method selected")
		exit(1)
		
def indexToZero(f, path, col, name="picopore.{}_index", dataColumn=None):
	dataset = f[path]
	name = name.format(col)
	data = f[path].value
	if not name in dataset.attrs.keys():
		dataColumn = data[col] if dataColumn is None else dataColumn
		start_index = min(dataColumn)
		dataset.attrs.create(name, start_index, dtype=getDtype(start_index))
		dataColumn = dataColumn-start_index
		data = drop_fields(data, [col])
		data = append_fields(data, [col], [dataColumn], [getDtype(dataColumn)])
	return data

def deepLosslessCompress(f, group):
	paths = findDatasets(f, group, "Events")
	paths = [path for path in paths if "Basecall" in path]
	# index event detection
	if "UniqueGlobalKey/channel_id" in f:
		sampleRate = f["UniqueGlobalKey/channel_id"].attrs["sampling_rate"]
		for path in paths:
			if f[path].parent.parent.attrs.__contains__("event_detection"):
				# index back to event detection
				dataset = f[path].value
				start = np.array([int(round(sampleRate * i)) for i in dataset["start"]])
				dataset = indexToZero(f, path, "start", dataColumn=start)
				move = dataset["move"] # rewrite move dataset because it's int64 for max 2
				# otherwise, event by event
				dataset = drop_fields(dataset, ["mean", "stdv", "length", "move"])
				dataset = append_fields(dataset, ["move"], [move], [getDtype(move)])
				rewriteDataset(f, path, compression="gzip", compression_opts=9, dataset=dataset)
				# rewrite eventdetection too - start is also way too big here
				eventDetectionPath = findDatasets(f, "all", entry_point=f[path].parent.parent.attrs.get("event_detection"))[0]
				if "picopore.start_index" not in f[eventDetectionPath].attrs.keys():
					eventData = indexToZero(f, eventDetectionPath, "start")
					rewriteDataset(f, eventDetectionPath, compression="gzip", compression_opts=9, dataset=eventData)
				
	if __basegroup_name__ not in f:
		f.create_group(__basegroup_name__)
		for name, group in f.items():
			if name != __basegroup_name__:
				recursiveCollapseGroups(f, __basegroup_name__, name, group)
	return losslessCompress(f, group)

def deepLosslessDecompress(f, group):
	# rebuild group hierarchy
	if __basegroup_name__ in f.keys():
		uncollapseGroups(f, f[__basegroup_name__])	
	paths = findDatasets(f, group)
	paths = [path for path in paths if "Basecall" in path]
	sampleRate = f["UniqueGlobalKey/channel_id"].attrs["sampling_rate"]
	for path in paths:
		if f[path].parent.parent.attrs.__contains__("event_detection"):
			# index back to event detection
			dataset = f[path].value
			if "mean" not in dataset.dtype.names:
				eventDetectionPath = findDatasets(f, "all", entry_point=f[path].parent.parent.attrs.get("event_detection"))[0]
				eventData = f[eventDetectionPath].value
				try:
					start = eventData["start"] + f[eventDetectionPath].attrs["picopore.start_index"]
					del f[eventDetectionPath].attrs["picopore.start_index"]
					eventData = drop_fields(eventData, ["start"])
					eventData = append_fields(eventData, ["start"], [start], [getDtype(start)])
					rewriteDataset(f, eventDetectionPath, compression="gzip", compression_opts=1, dataset=eventData)
				except KeyError:
					# must have been compressed without start indexing
					pass
				try:
					start_index = f[path].attrs["picopore.start_index"]
					del f[path].attrs["picopore.start_index"]
				except KeyError:
					# must have been compressed without start indexing
					start_index=0
				start = dataset["start"][0] + start_index
				end = dataset["start"][-1] + start_index
				# constrain to range in basecall
				eventData = eventData[np.logical_and(eventData["start"] >= start, eventData["start"] <= end)]
				# remove missing events
				i=0
				keepIndex = []
				for time in dataset["start"]:
					while eventData["start"][i] != time + start_index and i < eventData.shape[0]:
						i += 1
					keepIndex.append(i)
				eventData = eventData[keepIndex]
				dataset = drop_fields(dataset, "start")
				start = [i/sampleRate for i in eventData["start"]]
				length = [i/sampleRate for i in eventData["length"]]
				dataset = append_fields(dataset, ["mean", "start", "stdv", "length"], [eventData["mean"], start, eventData["stdv"], length])	
				rewriteDataset(f, path, dataset=dataset)
	return losslessDecompress(f, group)

def losslessCompress(f, group):
	paths = findDatasets(f, group, keyword="Events")
	paths.extend(findDatasets(f, group, keyword="Alignment"))
	paths.extend(findDatasets(f, "all", keyword="Signal", entry_point="Raw"))
	for path in paths:
		rewriteDataset(f, path, "gzip", 9)
	return "GZIP=9"
		
def losslessDecompress(f, group):
	paths = findDatasets(f, group, keyword="Events")
	paths.extend(findDatasets(f, group, keyword="Alignment"))
	paths.extend(findDatasets(f, "all", keyword="Signal", entry_point="Raw"))
	for path in paths:
		rewriteDataset(f, path)
	return "GZIP=1"

def rawCompressFastqSummary(f, group):
	return rawCompress(f, group, __raw_compress_keywords__)
	
def rawCompressFastqNoSummary(f, group):
	keywords = __raw_compress_keywords__
	keywords.append("Summary")
	return rawCompress(f, group, keywords)

def rawCompressSummaryNoFastq(f, group):
	keywords = __raw_compress_keywords__
	keywords.append("BaseCalled")
	return rawCompress(f, group, keywords)

def rawCompressMinimal(f, group):
	keywords = __raw_compress_keywords__
	keywords.append("Analyses")
	return rawCompress(f, group, keywords)

def rawCompress(f, group, keywords):
	paths = []
	for kw in keywords:
		paths.extend(findDatasets(f, group, keyword=kw))
	for path in paths:
		try:
			del f[path]
		except KeyError:
			# duplicated in paths, already deleted
			pass
	return "GZIP=9"

def compress(func, filename, group="all", prefix=None):
	if prefix is not None:
		newFilename = getPrefixedFilename(filename, prefix)
		copyfile(filename, newFilename)
	else:
		newFilename = filename
	try:
		with h5py.File(newFilename, 'r+') as f:
			filtr = func(f, group)
		subprocess.call(["h5repack","-f",filtr,newFilename, "{}.tmp".format(newFilename)])
		subprocess.call(["mv","{}.tmp".format(newFilename),newFilename])
	except Exception as e:
		log(str(e))

def compressWrapper(args):
	return compress(*args)
