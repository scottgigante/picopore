import subprocess
import os

__test_files__ = ["../sample_data/albacore_1d_original.fast5", "../sample_data/metrichor_2d_original.fast5"]
__test_runs__ = ["--test lossless", "--test deep-lossless"]
__prefix__ = "picopore.test"
__prefixed_runs__ = ["raw"]

def testFile(filename):
	for run in __test_runs__:
		subprocess.call("picopore -y {} {}".format(run, filename))
	for run in __prefixed_runs__:
		subprocess.call("picopore -y --prefix {} {} {}".format(__prefix__, run, filename))
		dirname = os.path.dirname(filename)
		basename = os.path.basename(filename)
		os.remove(os.path.join(dirname,".".join([__prefix__,basename])))
				