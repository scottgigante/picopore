import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
  name = 'picopore',
  packages = ['picopore'], # this must be the same as the name above
  version = '0.1.1',
  description = 'A tool for reducing the size of Oxford Nanopore Technologies\' datasets without losing information.',
  long_description=read('README'),
  author = 'Scott Gigante',
  author_email = 'scottgigante@gmail.com',
  url = 'https://github.com/scottgigante/picopore', # use the URL to the github repo
  download_url = 'https://github.com/scottgigante/picopore/tarball/0.1.0', 
  keywords = ['nanopore', 'compression', 'hdf5', 'fast5', 'oxford', 'minion'], # arbitrary keywords
  classifiers = ["Development Status :: 3 - Alpha"],
  entry_points = {
        'console_scripts': ['picopore=picopore.picopore:main'],
    },
)