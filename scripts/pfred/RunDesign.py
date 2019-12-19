#! /usr/bin/env python3

import sys
import logging
import inspect
import sequenceservice
import parserservice
import projectloghandler as hlr
import utilitiesservice as utils
import bowtieservice as bowtie
from exceptionlogger import ExceptionLogger
from parserservice import ParserService
from multiprocessing import Pool


filehandler = True


def prepareProjHandler(wfile=False, name='LogFile-pfred' + str(utils.pid())):
    # Define what the logger is going to be

    global logger
    hlr.logHandler(file=wfile, filename=name)
    logger = ExceptionLogger.create_logger(hlr.ch, logging.INFO, __name__)

    # Prepare handler for all services

    sequenceservice.logHandler(logfile=wfile, fname=name)
    parserservice.logHandler(logfile=wfile, fname=name)
    utils.logHandler(logfile=wfile, fname=name)
    bowtie.logHandler(logfile=wfile, fname=name)


def prepareInput(parser, flags, desta, helpa):

    myinput = []

    for flag, des, h in zip(flags, desta, helpa):
        parser.add_argument(flag, type=str, action='store', required=True,
                            dest=des, help=h)
    args = parser.parse_args()
    args = vars(args)

    for key, item in args.items():
        myinput.append(item)

    myinput.pop(0)
    myfile = inspect.getfile(inspect.currentframe())

    parser.showRun(myfile, flags, myinput)

    return myinput


def getOrthologs(parser):
    # Get orthologs part

    # Parse input

    flags = ['-g', '-s', '-l', '-o']
    desta = ['id', 'inputSpecies', 'requestedSpeciesList', 'outfile']
    helpa = ['Species ID, could be Ensembl or gene ID',
             'Input species common name',
             'requested species common names list spearated by ,',
             'Output file in CSV format']

    finput = prepareInput(parser, flags, desta, helpa)
    id = finput[0]
    id = id.strip()
    inputSpecies = finput[1]
    requestedSpeciesl = finput[2]
    requestedSpeciesl = parser.listFromInput(requestedSpeciesl,
                                             inputSpecies, ',')
    outfile = finput[3]

    # Create data

    seq = sequenceservice.SeqService()
    seq.validSpecies()
    reqspfull = seq.getFullNames(requestedSpeciesl)
    inspfull = seq.getFullNames(inputSpecies)

    logger.info(reqspfull)

    seq.createFullSpeciesl(inspfull, reqspfull)
    seq.checkSpeciesInput(inspfull, id)
    orthogenes = seq.getAllOrthologGenes(id, inspfull, reqspfull)
    seq.getSpeciesObjs(orthogenes)
    transdic = seq.getAllTranscripts(orthogenes)
    translist = utils.flattenDic(transdic)
    seq.getSeqs(translist, 'cdna')
    msg = seq.prepareOrthologData()

    header = ['name', 'species', 'length', 'source']
    utils.createOutCsv(header, msg, outfile)
    seq.createFastaFile('sequence.fa')


def getSeqTranscripts(parser):
    # Parse input

    flags = ['-l', '-f', '-a', '-v']
    desta = ['transcripts', 'sequencefile', 'exonfile', 'variationfile']
    helpa = ['Transcript ID list',
             'Fasta file',
             'Out file for exon boundaries in CSV format',
             'variation out file in CSV format']

    finput = prepareInput(parser, flags, desta, helpa)
    transcripts = finput[0]
    transcripts = parser.listFromInput(transcripts, '', ',')
    fasta = finput[1]
    outexon = finput[2]
    outvar = finput[3]
    # ntries = 15

    # Enumerate part

    seq = sequenceservice.SeqService()
    seq.getSpeciesObjs(transcripts)
    seq.getSeqsfromFasta(fasta, transcripts)

    seq.getUTRs(transcripts)

    header = ['sequenceName', 'columnNumber', 'residueNumber', 'number',
              'RCOL', 'GCOL', 'BCOL', 'SYMBOL', 'name', '5utrEnd', 'exonEnd']

    msg = seq.prepareBoundaryData(transcripts)
    utils.createOutCsv(header, msg, outexon)

    # Variations part

    # trans = [(tran, ntries) for tran in transcripts]

    # with Pool(len(transcripts)) as p:
    #     p.map(seq.getVariations, trans)

    seq.getVariations(transcripts)

    header = ['sequenceName', 'columnNumber', 'residueNumber', 'number',
              'RCOL', 'GCOL', 'BCOL', 'SYMBOL', 'name', 'snpId',
              'allele', 'snpType']

    msg = seq.prepareVariationData(transcripts)

    utils.createOutCsv(header, msg, outvar)


def callBowtieEnumerate(parser):
    # Bowtie part

    # Parse input

    flags = ['-p', '-l', '-f', '-o']
    desta = ['target', 'oligolen', 'fastafile', 'outfile']
    helpa = ['Target ID',
             'Oligo Length',
             'FASTA file',
             'out file']

    finput = prepareInput(parser, flags, desta, helpa)
    target = finput[0]
    oligolen = int(finput[1])
    fasta = finput[2]
    outf = finput[3]

    seq = sequenceservice.SeqService()
    seqdic = seq.getSeqsfromFasta(fasta, target)
    transcripts = seq.getIDsfromFasta(fasta)

    header = ['name', 'start', 'end', 'length', 'parent_dna_oligo',
              'parent_sense_oligo', 'parent_antisense_oligo', 'target_name']

    for tran in transcripts:
        header.append(tran + '_match')
        header.append(tran + '_position')

    sequence = seqdic[target]
    seq.enumerateSeq(sequence, oligolen)
    enumoligos = [seq.dnaoligos, seq.rnaoligos, seq.rnaasos]
    bow = bowtie.BowtieService(fasta)
    bow.prepareInput(target, enumoligos)
    bow.search()
    bow.parseOutput()
    bow.writeOligoOut(header, outf, transcripts, enumoligos, oligolen,
                      target)
    bow.cleanUp()


def joinOligoOut(parser):
    # Join Oligo part

    # Parse input

    flags = ['-l', '-j', '-v', '-o']
    desta = ['oligoout', 'exonboundaries', 'variation', 'output']
    helpa = ['Oligo output from Bowtie',
             'Exon boundaries out',
             'Variation file',
             'Output summary file']

    finput = prepareInput(parser, flags, desta, helpa)
    oligout = finput[0]
    exonfile = finput[1]
    variation = finput[2]
    outf = finput[3]

    seq = sequenceservice.SeqService()
    [file, reader] = utils.readAnnotationCsv(exonfile)
    seq.assignExons(reader)
    file.close()
    [file, reader] = utils.readAnnotationCsv(variation)
    seq.assignSNPs(reader)
    file.close()
    [file, reader] = utils.readAnnotationCsv(oligout)
    seq.createOligoOut(outf, reader)
    file.close()


def createBowtieIndexes(parser):

    flags = ['-s', '-n', '-t', '-d', '-u', '-m', '-c', '-r', '-f']
    desta = ['species', 'nthreads', 'seqtypes',
             'download', 'unspliced', 'mworkers',
             'decompress', 'ntries', 'tempdir']
    helpa = ['Species regular names', 'number of parallel threads',
             'sequence types', 'should I download the sequence files',
             'Should I build the unspliced sequence files',
             'Use multiple workers to create one single fasta file',
             'Which tool to decompress', 'How many retries in case url \
             stops sending data', 'temp directory to store downloads']

    finput = prepareInput(parser, flags, desta, helpa)
    requestedSpeciesl = finput[0]
    requestedSpeciesl = parser.listFromInput(requestedSpeciesl,
                                             '', ',')
    nthreads = int(finput[1])
    seqtype = finput[2]
    seqtype = parser.listFromInput(seqtype, '', ',')
    download = finput[3]
    unspliced = finput[4]
    mworkers = finput[5]
    dfun = finput[6]
    ntries = finput[7]
    tmpdir = finput[8]

    # Create data

    seq = sequenceservice.SeqService()
    seq.validSpecies()
    reqspfull = seq.getFullNames(requestedSpeciesl)
    logger.info(reqspfull)
    bow = bowtie.BowtieService('')
    bow.buildBowtieIndexesfromEnsemblGenomicSeq(seqtype,
                                                reqspfull, seq.getIDsfromFasta,
                                                nthreads,
                                                tmpdir=tmpdir,
                                                download=download,
                                                unspliced=unspliced,
                                                mworkers=mworkers,
                                                fun=dfun,
                                                ntries=ntries)


def main():
    FUNCTION_MAP = {'getOrthologs': getOrthologs,
                    'getSeqTranscripts': getSeqTranscripts,
                    'callBowtieEnumerate': callBowtieEnumerate,
                    'joinOligoOut': joinOligoOut,
                    'createBowtieIndexes': createBowtieIndexes}

    prepareProjHandler(wfile=filehandler)

    parser = ParserService(description='Choose design part')
    parser.add_argument('command', help='Design function to run',
                        choices=FUNCTION_MAP.keys())
    args = parser.parse_args(sys.argv[1:2])

    func = FUNCTION_MAP[args.command]
    func(parser)
    hlr.ch.flush()


if __name__ == '__main__':
    main()
