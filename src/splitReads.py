#!/usr/bin/python

# -*- coding: utf-8 -*-
"""
split big fasta/q into small files to process

Created on Wed Jan 28 14:51:36 EST 2015
@author: cjg
"""
import sys, os
import argparse
import time
import re
import argparse

## =================================================================
## Function: getRead
## =================================================================
def getReadFromFasta(fin):
    output = ""
    for line in fin:
        if line.strip("\n").strip() != "":
            if line[0] != ">":
                output += line
            else:
                if output != "":
                    yield output
                output = line
    yield output

def getReadFromFastq(fin):
    output = ""
    count = 0
    for line in fin:
        if count != 4:
            output += line
            count = count + 1
        else:
            yield output
            output = line
            count = 1
    yield output

def getHMMFromFile(fin):
    output = ""
    length = 0
    for line in fin:
        output += line
        if line[:4] == "LENG":
            length = int(line[5:-1].strip())
        elif line == "//\n":
            yield output, length
            output = ""
    yield output,length


## =================================================================
## Function: splitReads
## =================================================================
def splitReads(inputFile, prefix, count, summary, bpcount):
    ''' Split big fasta/fastq file into smaller ones, each contains a number of reads.
        Input:  inputFile - big file to split
                count - number of reads in each small file
                lengthCutoff - Only save reads that are longer than this length
                pair - If reads are interleaved in fastq file, if so, do not split a pair
        Output: prefix_03d.fasta/q
    '''
    fileExt = inputFile.split(".")[-1] # file type, fasta or fastq, autodetect
    if fileExt in ["fa", "Fa", "faa", "Faa", "fna", "Fna", "fasta", "Fasta"]:  # either fa or fq
        fileType = "fasta" 
    elif fileExt in ["fq", "Fq", "fastq", "Fastq"]:  # either fa or fq
        fileType = "fastq" 
    elif fileExt == "hmm":
        fileType = "hmm"
    else:
        sys.stderr.write("File type is not correct...\n") 


    fileCount = 1
    summary.write("file_name\tmax_len\tmin_len\n")
    outFileName = "{}{}.{}".format(prefix, fileCount, fileType)
    fout = open(outFileName, 'w')
    readCount = 0
    max_read_len = 0
    min_read_len = 100000
    sys.stderr.write("number of records in each file:{}\n".format(count))
    with open(inputFile,'r') as fin:
        if fileType == "fastq":
            for readLines in getReadFromFastq(fin):
                fout.write(readLines)
                seq_len = len(readLines.split("\n")[1])
                max_read_len = max_read_len if max_read_len > seq_len else seq_len
                min_read_len = min_read_len if min_read_len < seq_len else seq_len
                readCount = readCount + (seq_len if bpcount else 1)
                if readCount >= count:
                    fout.close()
                    summary.write("{}\t{}\t{}\n".format(outFileName, max_read_len, min_read_len))
                    max_read_len = 0
                    min_read_len = 100000
                    fileCount = fileCount + 1
                    outFileName = "{}{}.{}".format(prefix, fileCount, fileType)
                    fout = open(outFileName, 'w')
                    readCount = 0
        elif fileType == "fasta":
            for readLines in getReadFromFasta(fin):
                fout.write(readLines)
                seq_len = sum(map(len, readLines.split("\n")[1:]))
                max_read_len = max_read_len if max_read_len > seq_len else seq_len
                min_read_len = min_read_len if min_read_len < seq_len else seq_len
                readCount = readCount + (seq_len if bpcount else 1)
                if readCount >= count:
                    fout.close()
                    summary.write("{}\t{}\t{}\n".format(outFileName, max_read_len, min_read_len))
                    max_read_len = 0
                    min_read_len = 100000
                    fileCount = fileCount + 1
                    outFileName = "{}{}.{}".format(prefix, fileCount, fileType)
                    fout = open(outFileName, 'w')
                    readCount = 0
        elif fileType == "hmm":
            for readLines,hmm_len in getHMMFromFile(fin):
                fout.write(readLines)
                max_read_len = max_read_len if max_read_len > hmm_len else hmm_len
                min_read_len = min_read_len if min_read_len < hmm_len else hmm_len
                readCount = readCount + (hmm_len if bpcount else 1)
                if readCount >= count:
                    fout.close()
                    summary.write("{}\t{}\t{}\n".format(outFileName, max_read_len, min_read_len))
                    max_read_len = 0
                    min_read_len = 100000
                    fileCount = fileCount + 1
                    outFileName = "{}{}.{}".format(prefix, fileCount, fileType)
                    fout = open(outFileName, 'w')
                    readCount = 0
    fout.close()
    if readCount > 0:
        summary.write("{}\t{}\t{}\n".format(outFileName, max_read_len, min_read_len))
    if readCount == 0:
        os.remove(outFileName)


## =================================================================
## argument parser
## =================================================================
parser = argparse.ArgumentParser(description="Split big sequence file in fasta/fastq format into small ones",
                                 prog = 'splitReads', #program name
                                 prefix_chars='-', # prefix for options
                                 fromfile_prefix_chars='@', # if options are read from file, '@args.txt'
                                 conflict_handler='resolve', # for handling conflict options
                                 add_help=True, # include help in the options
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter # print default values for options in help message
                                 )

## input files and directories
parser.add_argument("-i","--in",help="input sequence file",dest='seqFile',required=True)

## output directory
parser.add_argument("-o","--out",help="output prefix",dest='outputPrefix',required=False)
parser.add_argument("-s","--summary",help="summary file",dest='summary',required=False, type=argparse.FileType('w'),default=sys.stdout)

## options
parser.add_argument("-c", "--count", help="number of sequences per file", dest='seqCount', required=False, default=10000, type=int)
#parser.add_argument("-l", "--length", help="length cutoff for the sequences", dest='lengthCutoff', required=False, default=1, type=int)
parser.add_argument("-v","--verbose",help="verbose, more output",action='store_true',dest='verbose')
parser.add_argument("-bp","--bpcount",help="instead of equal number of sequences, do equal number of bps/aas/residues",action='store_true',dest='bpcount')
## =================================================================
## main function
## =================================================================
def main(argv=None):
    
    if argv is None:
        args = parser.parse_args()

    if args.outputPrefix is None:
        args.outputPrefix = os.path.abspath(args.seqFile).split(".")[0]
    if args.verbose:
        sys.stderr.write("Input file is {}\n".format(args.seqFile))
        sys.stderr.write("Output file is {}\n".format(args.outputPrefix))
        #sys.stderr.write("Length cutoff is {}\n".format(args.lengthCutoff))
        sys.stderr.write("Number of sequences in each file is {}\n".format(args.seqCount))
        if args.bpcount:
            sys.stderr.write("Count bps/aas/residues instead of number of sequences/hmms\n")


    sys.stderr.write("\n===========================================================\n")
    start_time = time.time()

    splitReads(args.seqFile, args.outputPrefix, args.seqCount, args.summary, args.bpcount)
    #with open(args.seqFile, 'r') as fin:
    #    for a in getReadFromFastq(fin):
    #        sys.stdout.write(">>>>\n{}".format(a))

    sys.stderr.write("total time :" + str(time.time() - start_time) +  " seconds")
    sys.stderr.write("\n===========================================================\nDone\n")
##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())
