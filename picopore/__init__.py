from subprocess import call
from util import log

if not call("type h5repack", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
	log("h5repack not installed. Aborting.")
	exit(1)