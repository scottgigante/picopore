# Picopore v 0.2.1 #

A tool for reducing the size of Oxford Nanopore Technologies' datasets without losing information.

Options:
- Lossless compression: reduces footprint without reducing the ability to use other nanopore tools by using HDF5's inbuilt gzip functionality
- Deep lossless compression: reduces footprint without removing any data by indexing basecalled dataset to the event detection dataset
- Raw compression: reduces footprint by removing event detection and basecall data, leaving only raw signal, configuration data and FASTQ
- Minimal compression: reduces footprint by removing event detection and basecall data, leaving only raw signal (not yet implemented)

Author: Scott Gigante, Walter & Eliza Hall Institute of Medical Research. 
Contact: [Email] (mailto:gigante.s@wehi.edu.au), [Twitter] (http://www.twitter.com/scottgigante)

## Installation ##

The latest stable version of Picopore is available on PyPi. Install it using ```pip install picopore```. For the bleeding edge, clone and install from GitHub.
```
git clone https://www.github.com/scottgigante/picopore
cd picopore
python setup.py install
```
Currently, ```h5py``` is only available on Windows via ```conda```. Picopore will be uploaded to ```conda``` in the near future.

### Requirements ###

Picopore requires ```h5repack``` from ```hdf5-tools```, which can be downloaded from https://support.hdfgroup.org/downloads/index.html or using ```sudo apt-get install hdf5-tools```.

Picopore requires the following Python packages:
* h5py
* watchdog (for real-time compression)

## Usage ##

```
usage: picopore [-h] [-v] [-y] [--revert] [--realtime | --test]
                [--prefix PREFIX] [-t THREADS] [-g GROUP]
                {lossless,deep-lossless,raw} [input [input ...]]
```
```
positional arguments:
  {lossless,deep-lossless,raw}
                        choose compression mode (default: deep-lossless)
  input                 list of directories or fast5 files to shrink

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show version number and exit
  -y                    skip confirm step
  --revert              reverts files to original size (lossless modes only)
  --realtime            monitor a directory for new reads and compress them in
                        real time
  --test                compress to a temporary file and check that all
                        datasets and attributes are equal (note: does not work
                        on pre-compressed files)
  --prefix PREFIX       add prefix to output files to prevent overwrite
  -t THREADS, --threads THREADS
                        number of threads (default: 1)
  -g GROUP, --group GROUP
                        group number allows discrimination between different
                        basecalling runs (default: all)
```

It is necessary to choose one compression mode out of ```lossless```, ```deep-lossless```, ```raw```, and ```minimal```. 

Note that only ```lossless``` and ```deep-lossless``` are options for ```--revert``.

## Compression Modes ##

Picopore compression allows most nanopore tools to operate unimpeded. We provide a list of software tools which can operate on compressed files unimpeded, and the process required to recover the necessary data if this is not possible.

| Functionality                     | Lossless |      Deep Lossless      | Raw                             | Minimal                       |
|:---------------------------------:|:--------:|:-----------------------:|:-------------------------------:|:-----------------------------:|
| Metrichor                         |     ✓    | ```picopore --revert``` |  ✓                              |    ✓                          | 
| nanonetcall                       |     ✓    | ```picopore --revert``` |  ✓                              |    ✓                          | 
| poretools fastq / poRe printfastq |     ✓    | ```picopore --revert``` |  ✓                              | ```nanonetcall / Metrichor``` | 
| nanopolish consensus              |     ✓    | ```picopore --revert``` |  ```nanonetcall / Metrichor```  | ```nanonetcall / Metrichor``` | 


## FAQs ##

### Why would I want to shrink my fast5 files? ###

Nanopore runs are big. Really big. Over a long period of time, the storage footprint of a Nanopore lab will increase to unsustainable levels.

A large proportion of the data stored in ONT's fast5 files is unnecessary for the average end-user; during the basecalling process, a large amount of intermediary data is generated, and for most users who simply need the FASTQ, this data is useless.

Picopore solves this problem. Without removing the raw signal or configuration data used for basecalling, Picopore removes the intermediary datasets to reduce the size of your Nanopore dataset.

### Do I lose functionality when using Picopore? ###

#### Lossless ###
Lossless compression uses HDF5's builtin compression, so all existing fast5 tools will work seamlessly. 
- Use case: power users who wish to reduce server storage footprint

#### Deep Lossless ####
Deep lossless compression modifies the structure of your fast5 file: any data extraction tools will not work until you run ```python picopore.py --revert deep-lossless [input]```.
- Use case: power users who wish to reduce the size of their files during data transfer, or for long-term storage

#### Raw ####
Raw compression removes the "squiggle-space" data. For most users, this data is not critical; the only tools we know of which use the squiggle-space data are ```nanopolish```, ```nanoraw``` and ```nanonettrain```. If you do not intend on using these tools, your tools will work as before. If you do intend to use these tools, the raw signal is retained, and you can resubmit the files for basecalling to generate new squiggle-space data.
- Use case: end users who are only interested in using the FASTQ data
- Use case: power users running local basecalling with limited local disk space, who wish to use FASTQ immediately and will submit reads to Metrichor at a later date

#### Minimal ####
Minimal compression removes all data not required to rerun basecalling on the fast5 files. This is only recommended for long-term storage, and requires files to be re-basecalled for any data to be retrieved.
- Use case: users storing historical runs for archive purposes, with no short-term plans to use these reads

### Do I lose any data when using Picopore? ###

Technically yes, but nothing that cannot be recovered. In the case where you need to access the data which has been removed, you can regenerate it using either picopore (on lossless compression) or using any basecaller provided by ONT (for other methods.) 

Note that, since ONT's base calling is continuously improving, the basecalls generated when re-basecalling your data may not be the same, but in fact higher quality than before. If it is important that you retain the squiggle-space of the original called sequence, it is recommended that you use a lossless compression method.

