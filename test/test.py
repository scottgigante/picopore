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
    print(" ".join(args))
    p = subprocess.call(args)
    if prefix is not None:
        filename = args[-1]
        dirname = os.path.dirname(filename)
        basename = os.path.basename(filename)
        os.remove(os.path.join(dirname,".".join([prefix,basename])))
    return p

def testFile(filename):
    result = 0
    for run in __test_runs__:
        result += call(["--test","--mode",run, filename])
        result += call(["--mode",run, filename], prefix=__prefix__)
    for run in __raw_runs__:
        result += call(["--mode","raw"] + run + [filename], prefix=__prefix__)
    return result

def testRealtime(mode, additionalArgs=None, directory="realtime"):
    __waittime = 10
    mkdir(directory)
    args = ["python","-m","picopore","-y","--realtime","--print-every","1"]
    if additionalArgs is not None:
        args.extend(additionalArgs)
    args.extend(["--mode",mode,directory])
    print(" ".join(args))
    p = subprocess.Popen(args)
    time.sleep(__waittime)
    for filename in __test_files__:
        shutil.copy(filename, directory)
        time.sleep(__waittime)
    p.send_signal(signal.SIGINT)
    p.wait()
    shutil.rmtree(directory)
    return p.returncode

exitcode = 0
for filename in __test_files__:
    exitcode += testFile(filename)

for mode in __test_runs__:
    exitcode += testRealtime(mode)
for mode in __raw_runs__:
    exitcode += testRealtime("raw", additionalArgs=mode)
exit(exitcode)
