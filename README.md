# Picopore v 0.1.0 #

A tool for reducing the size of Oxford Nanopore Technologies' datasets without losing information.

Options:
- Lossless compression: reduces footprint without reducing the ability to use other nanopore tools by using HDF5's inbuilt gzip functionality
- Raw compression: reduces footprint by removing event detection and basecall data, leaving only raw signal, configuration data and FASTQ
- Deep lossless compression: reduces footprint without removing any data by indexing basecalled dataset to the event detection dataset (not yet implemented)

## Usage ##

```
usage: python picopore.py [-h] [--lossless] [--raw] [-t THREADS] [-g GROUP] [-y] {shrink, unshrink} [input]
```

```
positional arguments:
  {shrink,unshrink}     	Choose between shrinking and unshrinking files
  input                 	List of directories or fast5 files to shrink

optional arguments:
  --help			show this help message and exit
  --lossless		shrinks files with no data loss
  --raw				reverts files to raw signal data only
  --threads THREADS	number of threads
  --group GROUP		Group number allows discrimination between different basecalling runs (default: all)
  -y				Skip confirm step
```

## Compression Modes ##

| Functionality        | Lossless | Deep Lossless | Raw | Minimal |
|:--------------------:|:--------:|:-------------:|:---:|:-------:|
| Metrichor            |    ✔     |       ✔       |  ✔  |    ✔    | 
| nanonetcall          |    ✔     |       ✔       |  ✔  |    ✔    | 
| poretools fastq      |    ✔     |       ✔       |  ✔  |    ✘    | 
| nanopolish consensus |    ✓     |       ✘       |  ✘  |    ✘    | 

## FAQs ##

### Why would I want to shrink my fast5 files? ###

Nanopore runs are big. Really big. Over a long period of time, the storage footprint of a Nanopore lab will increase to unsustainable levels.

A large proportion of the data stored in ONT's fast5 files is unnecessary for the average end-user; during the basecalling process, a large amount of intermediary data is generated, and for most users who simply need the FASTQ, this data is useless.

Picopore solves this problem. Without removing the raw signal or configuration data used for basecalling, Picopore removes the intermediary datasets to reduce the size of your Nanopore dataset.

### Do I lose functionality when using Picopore? ###

Lossless compression uses HDF5's builtin compression, so all existing fast5 tools will work seamlessly. 
- Use case: power users who wish to reduce server storage footprint

Deep lossless compression modifies the structure of your fast5 file: any tools which use the "squiggle-space" data are not guaranteed to work until you run ```python picopore.py -d unshrink [input]```. The tools which use this data (that we know of) are listed below.
- Use case: power users who wish to reduce the size of their files during data transfer, or for long-term storage

Raw compression removes the "squiggle-space" data. For most users, this data is not critical; the only tools we know of which use the squiggle-space data are ```nanopolish```, ```nanoraw``` and ```nanonettrain```. If you do not intend on using these tools, your tools will work as before. If you do intend to use these tools, the raw signal is retained, and you can resubmit the files for basecalling to generate new squiggle-space data.
- Use case: end users who are only interested in using the FASTQ data
- Use case: power users running local basecalling with limited local disk space, who wish to use FASTQ immediately and will submit reads to Metrichor at a later date
