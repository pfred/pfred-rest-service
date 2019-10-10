#! /usr/bin/env python3
# Change in container code to /home/pfred/bin/python-3.6.2/bin/env python3

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


filehandler = False


def prepareProjHandler(wfile=False, name='LogFile-pfred'):
    global logger
    hlr.logHandler(file=wfile, filename=name)
    logger = ExceptionLogger.create_logger(hlr.ch, logging.INFO, __name__)
    sequenceservice.logHandler(logfile=wfile, fname=name)
    parserservice.logHandler(logfile=wfile, fname=name)
    utils.logHandler(logfile=wfile, fname=name)
    bowtie.logHandler(logfile=wfile, fname=name)


@ExceptionLogger(None, ZeroDivisionError, hlr.ch, "")
def divide():
    return 1 / 1


def prepareInput():

    myinput = []
    flags = ['-g', '-s', '-l', '-o']

    parser = ParserService(description='Provide gene \
                           ID and species of interest \
    in order to get orthologs')

    parser.add_argument(flags[0], type=str, action='store', required=True,
                        dest="id", help='Species ID, could be Ensembl \
                        or gene ID')

    parser.add_argument(flags[1], type=str, action='store', required=True,
                        dest="inputSpecies", help='Input species common name')

    parser.add_argument(flags[2], type=str, action='store', required=True,
                        dest="requestedSpeciesList", help='requested species common names list \
                        separated by ,')

    parser.add_argument(flags[3], type=str, action='store', required=True,
                        dest="outfile", help='Output file in csv format')

    args = parser.parse_args()

    myinput.append(args.id)
    myinput.append(args.inputSpecies)
    myinput.append(parser.listFromInput(args.requestedSpeciesList,
                                        args.inputSpecies, ","))
    myinput.append(args.outfile)

    myfile = inspect.getfile(inspect.currentframe())

    parser.showRun(myfile, flags, myinput)

    return myinput


# ENSEMBLID: ENSG00000165175
# Requested Species: rat
# Species: Human

# if __name__ == '__main__':

# Get Orthologs part

prepareProjHandler(wfile=filehandler)
finput = prepareInput()
id = finput[0]
id = id.strip()
inputSpecies = finput[1]
requestedSpeciesl = finput[2]
outfile = finput[3]
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
seqdic = seq.getSeqs(translist, 'cdna')
msg = seq.prepareOrthologData()

header = ['name', 'species', 'length', 'source']
utils.createOutCsv(header, msg, outfile)
seq.createFastaFile('sequence.fa')

# Enumerate part

transcripts = translist

seq.getSpeciesObjs(transcripts)

seq.getUTRs(transcripts)

header = ['sequenceName', 'columnNumber', 'residueNumber', 'number',
          'RCOL', 'GCOL', 'BCOL', 'SYMBOL', 'name', '5utrEnd', 'exonEnd']

outfile = 'exonBoundaries.csv'
msg = seq.prepareBoundaryData()
utils.createOutCsv(header, msg, outfile)

# Variations part

with Pool(len(transcripts)) as p:
    p.map(seq.getVariations, transcripts)

header = ['sequenceName', 'columnNumber', 'residueNumber', 'number',
          'RCOL', 'GCOL', 'BCOL', 'SYMBOL', 'name', 'snpId',
          'allele', 'snpType']

outfile = 'variantionData.csv'
msg = seq.prepareVariationData()

utils.createOutCsv(header, msg, outfile)

# Bowtie part

header = ['name', 'start', 'end', 'length', 'parent_dna_oligo',
          'parent_sense_oligo', 'parent_antisense_oligo', 'target_name']

for tran in transcripts:
    header.append(tran + '_match')
    header.append(tran + '_position')

sequence = seqdic['ENST00000378474']
seq.enumerateSeq(sequence, 14)
enumoligos = [seq.dnaoligos, seq.rnaoligos, seq.rnaasos]
bow = bowtie.BowtieService('sequence.fa')
bow.prepareInput('ENST00000378474', enumoligos)
bow.search()
bow.parseOutput()
bow.writeOligoOut(header, 'oligoout.csv', transcripts, enumoligos, 14,
                  'ENST00000378474')
bow.cleanUp()

# Join Oligo part

reader = utils.readAnnotationCsv('exonBoundaries.csv')
seq.assignExons(reader)
reader = utils.readAnnotationCsv('variantionData.csv')
seq.assignSNPs(reader)
reader = utils.readAnnotationCsv('oligoout.csv')
seq.createOligoOut('outputSummary_.csv', reader)

hlr.ch.flush()
