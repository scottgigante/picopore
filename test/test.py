import subprocess
import os
import errno
import shutil
import time

__test_files__ = ["sample_data/albacore_1d_original.fast5", "sample_data/metrichor_2d_original.fast5"]
__test_runs__ = ["lossless", "deep-lossless"]
__prefix__ = "picopore.test"
__raw_runs__ = [["--fastq","--summary"],["--summary","--no-fastq"],["--fastq","--no-summary"],["--no-fastq","--no-summary"]]

def mkdir(path):
	try:
		os.makedirs(path)
	except OSError as e:
		if e.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else:
			raise

def call(additionalArgs, prefix=None):
	args=["python","-m","picopore","-y"]
	if prefix is not None:
		args.extend(["--prefix",prefix])
	args.extend(additionalArgs)
	p = subprocess.call(args)
	if prefix is not None:
		filename = args[-1]
		dirname = os.path.dirname(filename)
		basename = os.path.basename(filename)
		os.remove(os.path.join(dirname,".".join([prefix,basename])))

def testFile(filename):
	for run in __test_runs__:
		call(["--test","--mode",run, filename])
		call(["--mode",run, filename], prefix=__prefix__)
	for run in __raw_runs__:
		call(["--mode","raw",run[0],run[1],filename], prefix=__prefix__)

def testRealtime(mode, additionalArgs=None, directory="realtime"):
	mkdir(directory)
	args = ["python","-m","picopore","-y","--realtime"]
	if additionalArgs is not None:
		args.extend(additionalArgs)
	args.extend(["--mode",mode,directory])
	p = subprocess.Popen(args)
	for filename in __test_files__:
		shutil.copy(filename, directory)
		time.sleep(2)
	p.kill()
	shutil.rmtree(directory)

for filename in __test_files__:
	testFile(filename)

for mode in __test_runs__:
	testRealtime(mode)
for mode in __raw_runs__:
	testRealtime("raw", additionalArgs=mode)
