import subprocess
import os

__test_files__ = ["sample_data/albacore_1d_original.fast5", "sample_data/metrichor_2d_original.fast5"]
__test_runs__ = ["lossless", "deep-lossless"]
__prefix__ = "picopore.test"
__prefixed_runs__ = ["lossless", "deep-lossless","raw"]

def testFile(filename):
	for run in __test_runs__:
		subprocess.call(["python","-m","picopore","-y","--test",run, filename])
	for run in __prefixed_runs__:
		subprocess.call(["python","-m","picopore","-y","--prefix",__prefix__, run, filename])
		dirname = os.path.dirname(filename)
		basename = os.path.basename(filename)
		os.remove(os.path.join(dirname,".".join([__prefix__,basename])))

for filename in __test_files__:
	testFile(filename)
