### Picopore v 0.0.1 ###

A tool for reducing the size of Oxford Nanopore Technologies' datasets without losing information.

Options:
- Lossless compression: reduces footprint without reducing the ability to use other nanopore tools by using HDF5's inbuilt gzip functionality
- Lossless deep compression: reduces footprint without removing any data by indexing basecalled dataset to the event detection dataset
- Utilitarian compression: reduces footprint by removing event detection and basecall data, leaving only raw signal and FASTQ
- Raw compression: reduces footprint by removing all data except raw signal.
