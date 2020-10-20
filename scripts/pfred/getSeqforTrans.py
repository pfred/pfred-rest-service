#! /usr/bin/env python3

import sys
import sequenceservice

fasta = "sequence.fa"


def getSeqforTrans(transcripts):
    seq = sequenceservice.SeqService()
    # seq.getSpeciesObjs(transcripts)
    seqdic = seq.getSeqsfromFasta(fasta, transcripts)

    print(seqdic[transcripts])


def main():
    getSeqforTrans(sys.argv[1])


if __name__ == '__main__':
    main()
