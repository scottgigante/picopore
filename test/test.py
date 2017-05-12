import subprocess
import os
import errno
import shutil
import time
import signal

__test_files__ = ["sample_data/albacore_1d_original.fast5", "sample_data/metrichor_2d_original.fast5"]
__test_runs__ = ["lossless", "deep-lossless"]
__prefix__ = "picopore.test"
__raw_runs__ = [["--fastq","--summary"],["--summary","--no-fastq"],["--fastq","--no-summary"],["--no-fastq","--no-summary"], ["--manual", "Analyses"]]

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def call(additionalArgs, prefix=None):
    args=["python","-m","picopore","-y","--print-every","1"]
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
    result = 0
    for run in __test_runs__:
        call(["--test","--mode",run, filename])
        call(["--mode",run, filename], prefix=__prefix__)
    for run in __raw_runs__:
        call(["--mode","raw"] + run + [filename], prefix=__prefix__)

def testRealtime(mode, additionalArgs=None, directory="realtime"):
    mkdir(directory)
    args = ["python","-m","picopore","-y","--realtime","--print-every","1"]
    if additionalArgs is not None:
        args.extend(additionalArgs)
    args.extend(["--mode",mode,directory])
    p = subprocess.Popen(args)
    time.sleep(15)
    for filename in __test_files__:
        shutil.copy(filename, directory)
        time.sleep(3)
    p.send_signal(signal.SIGINT)
    shutil.rmtree(directory)

for filename in __test_files__:
    testFile(filename)

for mode in __test_runs__:
    testRealtime(mode)
for mode in __raw_runs__:
    testRealtime("raw", additionalArgs=mode)
