from subprocess import call, PIPE
from util import log

if not call("type h5repack", shell=True, stdout=PIPE, stderr=PIPE) == 0:
	log("h5repack (hdf5-tools) not installed. Aborting.")
	exit(1)
