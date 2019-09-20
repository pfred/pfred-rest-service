#! /usr/bin/env python3
# Change in container code to /home/pfred/bin/python-3.6.2/bin/env python3

import logging
import inspect
from projectloghandler import ch
from exceptionlogger import ExceptionLogger
from sequenceservice import SeqService
from parserservice import ParserService
from multiprocessing import Pool


logger = ExceptionLogger.create_logger(ch, logging.INFO, __name__)


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

finput = prepareInput()
id = finput[0]
id = id.strip()
inputSpecies = finput[1]
requestedSpeciesl = finput[2]
outfile = finput[3]
seq = SeqService()
seq.validSpecies()
reqspfull = seq.getFullNames(requestedSpeciesl)
inspfull = seq.getFullNames(inputSpecies)

logger.info(reqspfull)

seq.createFullSpeciesl(inspfull, reqspfull)
seq.checkSpeciesInput(inspfull, id)
orthogenes = seq.getAllOrthologGenes(id, inspfull, reqspfull)
seq.getSpeciesObjs(orthogenes)
transdic = seq.getAllTranscripts(orthogenes)
translist = seq.flattenDic(transdic)
seqdic = seq.getSeqs(translist, 'cdna')
msg = seq.prepareOrthologData()

header = ['name', 'species', 'length', 'source']
seq.createOutCsv(header, msg, outfile)

# Enumerate part

transcripts = translist

seq.getSpeciesObjs(transcripts)

seq.getUTRs(transcripts)

header = ['sequenceName', 'columnNumber', 'residueNumber', 'number',
          'RCOL', 'GCOL', 'BCOL', 'SYMBOL', 'name', '5utrEnd', 'exonEnd']

outfile = 'exonBoundaries.csv'
msg = seq.prepareBoundaryData()
seq.createOutCsv(header, msg, outfile)

# Variations part

with Pool(len(transcripts)) as p:
    p.map(seq.getVariations, transcripts)

header = ['sequenceName', 'columnNumber', 'residueNumber', 'number',
          'RCOL', 'GCOL', 'BCOL', 'SYMBOL', 'name', 'snpId',
          'allele', 'snpType']

outfile = 'variantionData.csv'
msg = seq.prepareVariationData()


seq.createOutCsv(header, msg, outfile)

ch.flush()

# db = MySQLdb.connect(host='useastdb.ensembl.org', user='anonymous', port=5306,
#                      database='ensembl_stable_ids_97')
# cursor = db.cursor()

