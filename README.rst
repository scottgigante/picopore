Picopore v 1.1.1a
=================

A tool for reducing the size of Oxford Nanopore Technologies' datasets without losing information.

If you find Picopore useful, please cite it at http://dx.doi.org/10.12688/f1000research.11022.1

Options: 

* Lossless compression: reduces footprint without reducing the ability to use other nanopore tools by using HDF5's inbuilt gzip functionality; 
* Deep lossless compression: reduces footprint without removing any data by indexing basecalled dataset to the event detection dataset; 
* Raw compression: reduces footprint by removing event detection and basecall data, leaving only raw signal, configuration data and a choice of FASTQ data, basecall summary, both or neither.

Author: Scott Gigante, Walter & Eliza Hall Institute of Medical
Research. Contact: `Email <mailto:gigante.s@wehi.edu.au>`_, `Twitter <http://www.twitter.com/scottgigante>`_

Installation
------------

Install via pypi
~~~~~~~~~~~~~~~~

The latest stable version of Picopore is available on PyPi. Install it using the following command:

::

    pip install picopore

Install via conda
~~~~~~~~~~~~~~~~~

Picopore and dependencies could also be installed using conda.

::

    conda install picopore -c bioconda -c conda-forge

Install from source
~~~~~~~~~~~~~~~~~~~

For the bleeding edge, clone and install from GitHub.

::

    git clone https://www.github.com/scottgigante/picopore
    cd picopore
    python setup.py install

Currently, ``h5py`` is only available on Windows via ``conda``.

Requirements
~~~~~~~~~~~~

Picopore runs on Python 2.7, 3.3, 3.4, or 3.5 with development headers (``python-dev`` or similar).

Picopore requires ``h5repack`` from ``hdf5-tools``, which can be
downloaded from https://support.hdfgroup.org/downloads/index.html or
using ``sudo apt-get install hdf5-tools`` or similar.

Picopore requires the following Python packages: 

* ``h5py`` 
* ``watchdog`` (for real-time compression)

In addition, ``h5py`` requires HDF5 1.8.4 or later (``libhdf5-dev`` or similar). Difficulties resolving dependencies of ``h5py`` can be resolved by installing from your package manager, using ``sudo apt-get install python-h5py`` or similar.

Usage
-----

::

    usage: picopore [-h] [-v] --mode {lossless,deep-lossless,raw} [--revert]
                    [--realtime | --test] [--fastq] [--summary] [--prefix PREFIX]
                    [-y] [-t THREADS] [-g GROUP]
                    [input [input ...]]

::

    positional arguments:
      input                 list of directories or fast5 files to shrink

    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show version number and exit
      --mode {lossless,deep-lossless,raw}
                            choose compression mode
      --revert              reverts files to original size (lossless modes only)
      --realtime            monitor a directory for new reads and compress them in
                            real time
      --test                compress to a temporary file and check that all
                            datasets and attributes are equal (lossless modes
                            only)
      --fastq, --no-fastq   retain FASTQ data (raw mode only) (Default: --fastq)
      --summary, --no-summary
                            retain summary data (raw mode only) (Default: --no-
                            summary)
      --prefix PREFIX       add prefix to output files to prevent overwrite
      -y                    skip confirm step
      -t THREADS, --threads THREADS
                            number of threads (Default: 1)
      -g GROUP, --group GROUP
                            group number allows discrimination between different
                            basecalling runs (Default: all)

It is necessary to choose one compression mode out of ``lossless``,
``deep-lossless``, and ``raw``.

Note that only ``lossless`` and ``deep-lossless`` are options for ``--revert``.

Compression Modes
-----------------

Picopore compression allows most nanopore tools to operate unimpeded. We
provide a list of software tools which can operate on compressed files
unimpeded, and the process required to recover the necessary data if
this is not possible.

====================== ============= ======================= ============================= =============================
Functionality           Lossless      Deep Lossless           Raw                           Raw ``--no-fastq``           
====================== ============= ======================= ============================= =============================
Metrichor               ✓             ``picopore --revert``   ✓                            ✓                
nanonetcall             ✓             ``picopore --revert``   ✓                            ✓                
poretools fastq         ✓             ``picopore --revert``   ✓                            ``nanonetcall / Metrichor``
poRe printfastq         ✓             ``picopore --revert``   ✓                            ``nanonetcall / Metrichor``
nanopolish consensus    ✓             ``picopore --revert``   ``nanonetcall / Metrichor``   ``nanonetcall / Metrichor``
====================== ============= ======================= ============================= =============================

FAQs
----

Why would I want to shrink my fast5 files?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Nanopore runs are big. Really big. Over a long period of time, the
storage footprint of a Nanopore lab will increase to unsustainable
levels.

A large proportion of the data stored in ONT's fast5 files is
unnecessary for the average end-user; during the basecalling process, a
large amount of intermediary data is generated, and for most users who
simply need the FASTQ, this data is useless.

Picopore solves this problem. Without removing the raw signal or
configuration data used for basecalling, Picopore removes the
intermediary datasets to reduce the size of your Nanopore dataset.

Do I lose functionality when using Picopore?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lossless
^^^^^^^^

Lossless compression uses HDF5's builtin compression, so all existing
fast5 tools will work seamlessly. 

- Use case: power users who wish to reduce server storage footprint

Deep Lossless
^^^^^^^^^^^^^

Deep lossless compression modifies the structure of your fast5 file: any
data extraction tools will not work until you run
``python picopore.py --revert --mode deep-lossless [input]``. 

- Use case: power users who wish to reduce the size of their files during data transfer, or for long-term storage

Raw
^^^

Raw compression removes the "squiggle-space" data. For most users, this
data is not critical; the only tools we know of which use the
squiggle-space data are ``nanopolish``, ``nanoraw`` and
``nanonettrain``. If you do not intend on using these tools, your tools
will work as before. If you do intend to use these tools, the raw signal
is retained, and you can resubmit the files for basecalling to generate
new squiggle-space data. 

- Use case: end users who are only interested in using the FASTQ data 
- Use case: power users running local basecalling with limited local disk space, who wish to use FASTQ immediately and will submit reads to Metrichor at a later date

Raw ``--no-fastq``
^^^^^^^^^^^^^^^^^^

Minimal compression removes all data not required to rerun basecalling
on the fast5 files. This is only recommended for long-term storage, and
requires files to be re-basecalled for any data to be retrieved. 

- Use case: users storing historical runs for archive purposes, with no short-term plans to use these reads

Do I lose any data when using Picopore?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Technically yes, but nothing that cannot be recovered. In the case where
you need to access the data which has been removed, you can regenerate
it using either picopore (on lossless compression) or using any
basecaller provided by ONT (for other methods.)

Note that, since ONT's base calling is continuously improving, the
basecalls generated when re-basecalling your data may not be the same,
but in fact higher quality than before. If it is important that you
retain the squiggle-space of the original called sequence, it is
recommended that you use a lossless compression method.
