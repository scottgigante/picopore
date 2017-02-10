import h5py
import sys
import os
from multiprocessing import Pool
from argparse import ArgumentParser
from __future__ import print_function

def parseArgs(argv):
	parser = ArgumentParser(argv, description="A tool for reducing the size of an Oxford Nanopore Technologies dataset without losing any data")
	parser.add_argument("-l", "--lossless", default=False, action="store_true", help="Shrinks files with no data loss")
	parser.add_argument("--raw", default=False, action="store_true", help="Reverts files to raw signal data only")
	parser.add_argument("-t", "--threads", type=int, default=1, help="number of threads")
	parser.add_argument("-g", "--group", default="all", help="Group number allows discrimination between different basecalling runs (default: all)")
	parser.add_argument("-y", type="store_true", default=False, help="Skip confirm step")
	parser.add_argument("command", nargs="1", choices=('shrink', 'unshrink')help="Choose between shrinking and unshrinking files", required=True)
	parser.add_argument("input", nargs="*", help="List of directories or fast5 files to shrink", required=True)

def findEvents(file, group_id):
	eventPaths = []
	analyses = file.get("Analyses")
	subgroups = analyses.items()
	for group in subgroups:
		if group_id = "all" or group.endswith(group_id):
			for event_group in group:
				eventPaths.append(event_group.name + "/Events") # TODO: is this right?
	return eventPaths
				
	
def rewriteDataset(file, path, compression, compression_opts):
	dataset = file.get(path)
	del file[path]
	file.create_dataset(path, dataset, compression=compression, compression_opts=compression_opts)
	
def losslessCompress(filename):
	with h5py.File(filename, 'r+') as file:
		eventsPath = "Analyses/Basecall_1D_000/BaseCalled_template/Events"
		rewriteDataset(file, eventsPath, "gzip", 9)
		
def losslessDecompress(filename):
	with h5py.File(filename, 'r+') as file:
		eventsPath = "Analyses/Basecall_1D_000/BaseCalled_template/Events"
		rewriteDataset(file, eventsPath, None, None)
		
def rawCompress(filename):
	with h5py.File(filename, 'r+') as file:
		basecallPath = "Analyses/Basecall_1D_000/BaseCalled_template/Events"
		eventsPath = "Analyses/EventDetection_000/BaseCalled_template/Events"
		del file[eventsPath]
		
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
		
def recursiveFindFast5(input):
	files = []
	for path in input:
		if os.path.isdir(path):
			files.extend(recursiveFindFast5(os.listdir(path)))
		elif os.path.isfile(path) and path.endswith(".fast5"):
			files.append(path)
	return files
	
def checkSure():
	response = input("Are you sure? (yes|no): ")
	if "yes".startswith(response):
		return 1
	else:
		return 0
	
def run(argv):
	args = parseArgs(argv)
	func = chooseShrinkFunc(args)
	fileList = recursiveFindFast5(args.input)
	print("on {} files... ".format(len(fileList)), end='', flush=True)
	if args.yes or checkSure():
		pool = Pool(args.threads)
		pool.map(func, fileList)
		print("Complete.")
	else:
		print("User cancelled. Exiting.")

if __name__ == "__main__":
	run(sys.argv)