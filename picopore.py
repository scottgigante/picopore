from __future__ import print_function
import h5py
import sys
import os
from multiprocessing import Pool
from argparse import ArgumentParser
from subprocess import Popen

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

def findEvents(file, group_id):
	eventPaths = []
	analyses = file.get("Analyses")
	for group in analyses.values():
		if group_id == "all" or group.endswith(group_id):
			for event_group in group.values():
				if "Events" in event_group.keys():
					eventPaths.append("{}/Events".format(event_group.name)) 
	return eventPaths	
	
def rewriteDataset(file, path, compression="gzip", compression_opts=4):
	dataset = file.get(path).value
	del file[path]
	file.create_dataset(path, data=dataset, dtype=dataset.dtype, compression=compression, compression_opts=compression_opts)

def losslessCompress(f, group):
	for path in findEvents(f, group):
		rewriteDataset(f, path, "gzip", 9)
	return "GZIP=9"

def compress(func, filename, group):
	with h5py.File(filename, 'r+') as f:
		filtr = func(f, group)
	Popen(["h5repack","-f",filtr,filename,"{}.tmp".format(filename)])
	Popen(["mv","{}.tmp".format(filename),filename])

def compressWrapper(args):
	return compress(*args)
		
def losslessDecompress(f, group):
	for path in findEvents(f, group):
		rewriteDataset(f, path)
	return "GZIP=4"

def losslessDecompressWrapper(args):
	return losslessDecompress(*args)
		
def rawCompress(f, group):
	for path in findEvents(f, group):
		del f[path]
	return "GZIP=9"

def rawCompressWrapper(args):
	return rawCompress(*args)
		
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
	
def run(argv):
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
	run(sys.argv)
