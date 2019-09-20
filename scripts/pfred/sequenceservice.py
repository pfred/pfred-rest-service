#! /usr/bin/env python3
# Change in container code to /home/pfred/bin/python-3.6.2/bin/env python3

import ensembl_rest
import logging
import multiprocessing
from projectloghandler import ch
from exceptionlogger import ExceptionLogger
from itertools import chain


class SeqService:
    def __init__(self):
        self.logger = ExceptionLogger.create_logger(ch, logging.INFO, __name__)
        self._species = {'mouse': 'mus_musculus',
                         'rat': 'rattus_norvegicus',
                         'human': 'homo_sapiens',
                         'dog': 'canis_familiaris',
                         'chimp': 'pan_troglodytes',
                         'macaque': 'macaca_mulatta'}
        self._mapdic = {}
        self._loggermsg = ""
        self.orthogenes = []
        self.allspecies = []
        self.matrixdata = []
        self._speciesobjs = {}
        self.transcriptdic = {}
        self.seqsdic = {}
        self.exondic = {}
        self.utrdic = {}
        manager = multiprocessing.Manager()
        self.varsdic = manager.dict()

    @ExceptionLogger("logger", ensembl_rest.HTTPError, ch, "_loggermsg")
    def setGen2CdnaMap(self, id, regioncdna):
        optional = {'include_original_region': 1}
        regioncdnas = [str(i) for i in regioncdna]
        regioncdnas = '..'.join(regioncdnas)
        self._mapdic[id] = ensembl_rest.assembly_cdna(id, regioncdnas,
                                                      params=optional)

    @ExceptionLogger("logger", KeyError, ch, "_loggermsg")
    def mapGen2Cdna(self, id, length):
        """
        Maps coordinates from cdna to genomic space
        """

        mapdic = self._mapdic[id]
        mapdic = mapdic['mappings']

        for mapi in mapdic:
            genomic = mapi['mapped']
            target = mapi['original']

            if(genomic['start'] <= length <= genomic['end']):
                return length - (genomic['end'] - target['end'])
        return None

    def flattenList(self, seqslist):
        return list((chain.from_iterable(seqslist)))

    def flattenDic(self, seqsdic):
        return sorted(set(chain(*seqsdic.values())))

    def createFullSpeciesl(self, inspecies, reqspecies):
        if isinstance(inspecies, str):
            self.allspecies = [inspecies] + reqspecies
        elif isinstance(reqspecies, str):
            self.allspecies = inspecies + [reqspecies]
        else:
            self.allspecies = inspecies + reqspecies

        return self.allspecies

    def validSpecies(self):
        msg = ["Valid species are"]
        for key, un in self._species.items():
            msg.append(key)
        msg = '\n'.join(msg)
        self._loggermsg = msg

    @ExceptionLogger("logger", KeyError, ch, "_loggermsg")
    def getSeqsLength(self, seqs):
        return [abs(seq['end'] - seq['start']) + 1 for seq in seqs]

    @ExceptionLogger("logger", KeyError, ch, "_loggermsg")
    def getSeqObjCumuLength(self, objs, condition, key='object_type'):
        """
        Given a list of objects, compute cumulative length on seq elements
        (e.g Exons, UTRs)
        that qualify under the given condition
        """
        return sum([obj['end'] - obj['start'] + 1
                   if (obj[key] == condition)
                   else 0 for obj in objs])

    @ExceptionLogger("logger", KeyError, ch, "_loggermsg")
    def getFullNames(self, species):
        """
        Convert common names into full names
        """

        if isinstance(species, str):
            return self._species[species]

        speciesfullnames = []

        for sp in species:
            speciesfullnames.append(self._species[sp])
        return speciesfullnames

    @ExceptionLogger("logger", KeyError, ch, "_loggermsg")
    def checkSpeciesInput(self, inspecies, spid):
        """
        Checks whether the input stable id matches the input species
        """
        self._loggermsg = ""
        species = ""

        try:
            species = ensembl_rest.lookup(spid)
        except ensembl_rest.HTTPError as e:
            self.logger.exception(str(e))

        species = species['species']
        if species == inspecies:
            self.logger.info("Input gene is {}, {}".format(species, spid))
            return 0
        self.logger.exception("Input species and given stable ID dont match")
        raise ValueError

    @ExceptionLogger("logger", ensembl_rest.HTTPError, ch, "_loggermsg")
    def getSpeciesObjs(self, spids):
        """
        Gets all objects from given species stable IDs
        """

        # Get All info from species

        if isinstance(spids, str):
            spids = [spids]

        optional = {'ids': spids, 'expand': 1, 'utr': 1}
        self._speciesobjs = ensembl_rest.lookup_post(params=optional)
        return self._speciesobjs

    @ExceptionLogger("logger", ensembl_rest.HTTPError, ch, "_loggermsg")
    def getAllOrthologGenes(self, ingene, inspec, reqspec):
        """
        Gets all orthologous genes for the input gene
        given the requested species
        """

        msg = []

        self.orthogenes.append(ingene)

        optional = {'target_species': reqspec, 'type': 'orthologues',
                    'cigar_line': 0}

        orthgene = ensembl_rest.homology_ensemblgene(ingene, params=optional)

        # Retrieve the gene ortholog data from homologies

        orthgene = orthgene['data']
        orthgene = orthgene[0]
        orthgenel = orthgene['homologies']

        # Store genes

        for elem in range(len(orthgenel)):
            orthgene = orthgenel[elem]
            orthgene = orthgene['target']
            orthgene = orthgene['id']
            self.orthogenes.append(orthgene)

        # logging info

        for gene, count in zip(self.orthogenes, range(len(self.orthogenes))):
            msg.append("Ortholog Gene {}: {}".format(count, gene))

        msg = '\n'.join(msg)
        self.logger.info(msg)

        return self.orthogenes

    @ExceptionLogger("logger", KeyError, ch, "_loggermsg")
    def getAllTranscripts(self, spids, species=None):
        """
        Gets all transcripts given the stable ids
        and returns as transcript id dictionary
        """

        if species is None:
            species = self._speciesobjs

        # Get transcripts

        for id in spids:
            tidl = []
            specy = species[id]
            transcripts = specy['Transcript']
            for trans in transcripts:
                tid = trans['id']
                tidl.append(tid)
            self.transcriptdic[specy['species']] = tidl

        return self.transcriptdic

    @ExceptionLogger("logger", ensembl_rest.HTTPError, ch, "_loggermsg")
    def getSeqs(self, spids, seqtype=None):
        """
        Gets FASTA sequences given stable ids
        """

        if isinstance(spids, str):
            spids = [spids]

        if seqtype is None:
            optional = {'ids': spids}
        else:
            optional = {'type': seqtype, 'ids': spids}

        seqs = ensembl_rest.sequence_id_post(params=optional)

        for spid, seq in zip(spids, seqs):
            self.seqsdic[spid] = seq['seq']

        return self.seqsdic

    @ExceptionLogger("logger", KeyError, ch, "_loggermsg")
    def getExons(self, spids, species=None):
        """
        Gets exon objects given stable ID
        """

        if species is None:
            species = self._speciesobjs

        # If it is ensemble transcript id, the key should be directly Exon

        if isinstance(spids, str):
            spids = [spids]

        for id in spids:
            specy = species[id]
            if specy.get('Transcript', None) is None:
                self.exondic[id] = specy['Exon']
            else:
                transcripts = specy['Transcript']
                for trans in transcripts:
                    self.exondic[id] = trans['Exon']

        return self.exondic

    def getVariations(self, spids, parallel=True, filtvalue='intron_variant',
                      vartype=None, species=None):
        """
        Gets variation objects given stable ID,
        filters variants based on variable filtvalue,
        if variable parallel is true, the function will
        be called in a multiprocessing pool
        """

        if species is None:
            species = self._speciesobjs

        if vartype is None:
            optional = {'feature': 'variation'}
        else:
            optional = {'feature': vartype}

        if parallel:
            if isinstance(spids, list):
                self.logger.exception(str(ValueError))
                raise ValueError
            try:
                self.varsdic[spids] = ensembl_rest.overlap_id(spids,
                                                              params=optional)
            except ensembl_rest.HTTPError as e:
                self.logger.exception(str(e))

            self.logger.info(spids)

            vars = self.varsdic[spids]
            self.varsdic[spids] = list(filter(lambda var:
                                              var['consequence_type'] !=
                                              filtvalue, vars))
        else:

            self.varsdic = {}

            if isinstance(spids, str):
                spids = [spids]

            for spid in spids:
                self.varsdic[spid] = ensembl_rest.overlap_id(spid,
                                                             params=optional)
                vars = self.varsdic[spid]
                self.varsdic[spid] = list(filter(lambda var:
                                                 var['consequence_type'] !=
                                                 filtvalue, vars))

    @ExceptionLogger("logger", KeyError, ch, "_loggermsg")
    def getUTRs(self, spids, species=None):
        """
        Gets UTR objects given stable ID
        """

        if species is None:
            species = self._speciesobjs

        # If it is ensemble transcript id, the key should be UTR directly

        if isinstance(spids, str):
            spids = [spids]

        for id in spids:
            specy = species[id]
            if specy.get('Transcript', None) is None:
                self.utrdic[id] = specy['UTR']
            else:
                transcripts = specy['Transcript']
                for trans in transcripts:
                    self.utrdic[id] = trans['UTR']

        return self.utrdic

    def prepareOrthologData(self):
        """
        Flattens ortholog transcript data structures into a matrix
        for csv format
        """

        matrixdata = []

        for spec in self.allspecies:
            [matrixdata.append([tid,  # Transcript ID
                                spec,  # Species name
                                len(self.seqsdic[tid]),  # Length of seq
                                'ENSEMBL'])  # From where
             for tid in self.transcriptdic[spec]]

        self.matrixdata = matrixdata

        return self.matrixdata

    def prepareBoundaryData(self):
        """
        Flattens boundary data structures into a matrix
        for csv format
        """

        matrixdata = []

        # Optimize this...

        for name, trans in self.transcriptdic.items():
            for tran in trans:
                utrs = self.utrdic[tran]
                fivedis = self.getSeqObjCumuLength(utrs, 'five_prime_UTR')
                threedis = self.getSeqObjCumuLength(utrs, 'three_prime_UTR')
                exondis = len(self.seqsdic[tran]) - threedis
                fiveutrexists = str(fivedis > 0).lower()
                exonsexist = str(exondis > 0).lower()
                nfiveutrexists = str(not(fiveutrexists)).lower()
                nexonexists = str(not(exonsexist)).lower()
                matrixdata.append([tran,  # Transcript ID
                                   '-1',  # -1
                                   fivedis,  # 5primes length
                                   '-1',
                                   '0.21',
                                   '0.7',
                                   '0.59',
                                   '*',
                                   'untitled',
                                   fiveutrexists, nfiveutrexists])

                matrixdata.append([tran,  # Transcript ID
                                   '-1',  # -1
                                   exondis,  # exons length
                                   '-1',
                                   '0.21',
                                   '0.7',
                                   '0.59',
                                   '*',
                                   'untitled',
                                   nexonexists, exonsexist])

        self.matrixdata = matrixdata
        return self.matrixdata

    def prepareVariationData(self):
        """
        Flattens boundary data structures into a matrix
        for csv format
        """

        matrixdata = []
        varsdic = self.varsdic
        genMapper = self.setGen2CdnaMap
        mapper = self.mapGen2Cdna

        # Optimize this...

        for name, trans in self.transcriptdic.items():
            for tran in trans:
                vars = varsdic[tran]
                if vars:
                    length = len(self.seqsdic[tran])
                    genMapper(tran, [1, length])
                    for var in vars:
                        coord = mapper(tran, var['start'])
                        if coord:
                            matrixdata.append([tran,
                                               '-1',
                                               coord,
                                               '-1',
                                               '0.21',
                                               '0.49',
                                               '0.84',
                                               '*',
                                               'untitled',
                                               var['id'],
                                               '/'.join(var['alleles']),
                                               var['consequence_type'].upper()])
        self.matrixdata = matrixdata
        return self.matrixdata

    @ExceptionLogger("logger", ValueError, ch, "_loggermsg")
    def createOutCsv(self, title, data, fname):
        """
        Creates output file given filename, data and title in csv format
        input data must be list of lists
        """

        msg = [",".join(title)]

        for row in data:
            msg.append(",".join(map(str, row)))

        msg = '\n'.join(msg)
        outhandler = open(fname, 'w')
        outhandler.write(msg)
        outhandler.close()
