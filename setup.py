from distutils.core import setup
setup(
  name = 'picopore',
  packages = ['picopore'], # this must be the same as the name above
  version = '0.1.0',
  description = 'A tool for reducing the size of Oxford Nanopore Technologies\' datasets without losing information.',
  author = 'Scott Gigante',
  author_email = 'scottgigante@gmail.com',
  url = 'https://github.com/scottgigante/picopore', # use the URL to the github repo
  download_url = 'https://github.com/scottgigante/picopore/tarball/0.1.0', # I'll explain this in a second
  keywords = ['nanopore', 'compression', 'hdf5', 'fast5', 'oxford', 'minion'], # arbitrary keywords
  classifiers = [],
)