import os
from setuptools import setup

version_py = os.path.join(os.path.dirname(__file__), 'picopore', 'version.py')
version = open(version_py).read().strip().split('=')[-1].replace('"','').strip()
print version

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
  name = 'picopore',
  packages = ['picopore'],
  package_dir={'picopore': "picopore"},
  version=version,
  install_requires=['h5py>2.2.0','watchdog'],
  requires=['python (>=2.7, <3.0)'],
  description = 'A tool for reducing the size of Oxford Nanopore Technologies\' datasets without losing information.',
  long_description=read('README.rst'),
  author = 'Scott Gigante',
  author_email = 'scottgigante@gmail.com',
  url = 'https://github.com/scottgigante/picopore', # use the URL to the github repo
  keywords = ['nanopore', 'compression', 'hdf5', 'fast5', 'oxford', 'minion'], # arbitrary keywords
  classifiers = [
		"Development Status :: 3 - Alpha",
		'Intended Audience :: Science/Research',
		'License :: OSI Approved :: GNU General Public License (GPL)',
		'Topic :: Scientific/Engineering :: Bio-Informatics'
		],
  entry_points = {
        'console_scripts': ['picopore = picopore.__main__:main'],
    },
)
