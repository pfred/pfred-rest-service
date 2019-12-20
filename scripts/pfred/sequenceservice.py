#! /usr/bin/env python3

import csv
import mmap
import ensembl_rest
import logging
import multiprocessing
import textwrap
import utilitiesservice as utils
import projectloghandler as hlr
from exceptionlogger import ExceptionLogger


def logHandler(fname, logfile=False):
    hlr.logHandler(file=logfile, filename=fname)


class SeqService:
    def __init__(self):
        self.logger = ExceptionLogger.create_logger(hlr.ch,
                                                    logging.INFO, __name__)
        self._species = {'mouse': 'mus_musculus',
                         'rat': 'rattus_norvegicus',
                         'human': 'homo_sapiens',
                         'dog': 'canis_familiaris',
                         'chimp': 'pan_troglodytes',
                         'macaque': 'macaca_mulatta'}
        manager = multiprocessing.Manager()
        self._subs = {'C': 'G', 'G': 'C', 'A': 'U', 'U': 'A', 'T': 'A'}
        self._subsdna = {'C': 'G', 'G': 'C', 'A': 'T', 'U': 'A', 'T': 'A'}
        self._mapdic = {}
        self._loggermsg = ""
        self.orthogenes = []
        self.allspecies = []
        self.matrixdata = []
        self.dnaoligos = []
        self.rnaoligos = []
        self.rnaasos = []
        self._speciesobjs = {}
        self._exonposdic = {}
        self._exonnamedic = {}
        self._snpdic = {}
        self.transcriptdic = {}
        self.seqsdic = {}
        self.exondic = {}
        self.utrdic = {}
        self.varsdic = manager.dict()

    @ExceptionLogger("logger", ensembl_rest.HTTPError, hlr.ch, "_loggermsg")
    def setGen2CdnaMap(self, id, regioncdna):
        optional = {'include_original_region': 1}
        regioncdnas = [str(i) for i in regioncdna]
        regioncdnas = '..'.join(regioncdnas)
        self._mapdic[id] = ensembl_rest.assembly_cdna(id, regioncdnas,
                                                      params=optional)

    @ExceptionLogger("logger", KeyError, hlr.ch, "_loggermsg")
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

    @ExceptionLogger("logger", KeyError, hlr.ch, "_loggermsg")
    def getSeqsLength(self, seqs):
        return [abs(seq['end'] - seq['start']) + 1 for seq in seqs]

    @ExceptionLogger("logger", KeyError, hlr.ch, "_loggermsg")
    def getSeqObjCumuLength(self, objs, condition, key='object_type'):
        """
        Given a list of objects, compute cumulative length on seq elements
        (e.g Exons, UTRs)
        that qualify under the given condition
        """
        return sum([obj['end'] - obj['start'] + 1
                   if (obj[key] == condition)
                   else 0 for obj in objs])

    @ExceptionLogger("logger", KeyError, hlr.ch, "_loggermsg")
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

    @ExceptionLogger("logger", KeyError, hlr.ch, "_loggermsg")
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

    @ExceptionLogger("logger", ValueError, hlr.ch, "_loggermsg")
    def rna2dna(self, seq):
        """
        Convert from RNA to DNA
        """
        dna = seq.replace('U', 'T')
        return dna

    @ExceptionLogger("logger", ValueError, hlr.ch, "_loggermsg")
    def cdna2rna(self, seq):
        """
        Convert from cDNA to RNA
        """
        rna = seq.replace('T', 'U')
        return rna

    @ExceptionLogger("logger", ValueError, hlr.ch, "_loggermsg")
    def getReverseComplement(self, seq, type):
        """
        Gets sequence and returns its reverse complement
        """

        reverse = ''.join(reversed(seq))

        if type == 'dna':
            return utils.replaceMultiple(reverse, self._subsdna)
        else:
            return utils.replaceMultiple(reverse, self._subs)

    @ExceptionLogger("logger", ValueError, hlr.ch, "_loggermsg")
    def enumerateSeq(self, seq, oligolen):
        """
        Enumerate given sequence
        """

        cdna2rna = self.cdna2rna
        getReverseComp = self.getReverseComplement

        dnaoligos = self.dnaoligos
        rnaoligos = self.rnaoligos
        rnaasos = self.rnaasos

        dna = self.rna2dna(seq)
        total = len(dna) - oligolen + 1

        for elem in range(total):
            endi = elem + oligolen
            subdna = dna[elem:endi]
            dnaoligos.append(subdna)
            rnaoligos.append(cdna2rna(subdna))
            rnaasos.append(getReverseComp(subdna, 'rna'))

        self.dnaoligos = dnaoligos
        self.rnaoligos = rnaoligos
        self.rnaasos = rnaasos

    @ExceptionLogger("logger", ValueError, hlr.ch, "_loggermsg")
    def getSeqsfromFasta(self, fasta, ids):
        """
        Get sequences from FASTA file and store in dictionary
        """
        if not(isinstance(ids, list)):
            ids = [ids]

        with open(fasta, 'rb', 0) as file, \
                mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:

            for gid in ids:
                if s.find(bytes(gid, 'utf-8')) != -1:
                    file.seek(0)
                    copy = False
                    sequence = []
                    for line in file:
                        line = line.decode('utf-8')
                        line = line.strip()
                        code = '>' + gid
                        if line == code:
                            copy = True
                            continue
                        elif line[0] == '>':
                            copy = False
                            continue
                        elif copy:
                            sequence.append(line)
                    self.seqsdic[gid] = ''.join(sequence)
            return self.seqsdic

    def getIDsfromFasta(self, fasta):
        """
        Get ENSEMBL IDs from FASTA file and store in dictionary
        """
        trans = []
        try:
            for line in open(fasta):
                if line.startswith('>'):
                    tran = line.strip()
                    tran = tran[1:]
                    tran = tran.split(' ')
                    trans.append(tran[0])
        except ValueError as e:
            self.logger.exception(str(e))
        return trans

    @ExceptionLogger("logger", ensembl_rest.HTTPError, hlr.ch, "_loggermsg")
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

    @ExceptionLogger("logger", ensembl_rest.HTTPError, hlr.ch, "_loggermsg")
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

    @ExceptionLogger("logger", KeyError, hlr.ch, "_loggermsg")
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
            # print(species)
            specy = species[id]
            transcripts = specy['Transcript']
            for trans in transcripts:
                tid = trans['id']
                tidl.append(tid)
            self.transcriptdic[specy['species']] = tidl

        return self.transcriptdic

    @ExceptionLogger("logger", ensembl_rest.HTTPError, hlr.ch, "_loggermsg")
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

    @ExceptionLogger("logger", KeyError, hlr.ch, "_loggermsg")
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
            spids, ntries = spids
            if isinstance(spids, list):
                self.logger.exception(str(ValueError))
                raise ValueError
            try:
                self.varsdic[spids] = ensembl_rest.overlap_id(spids,
                                                              params=optional)
            except ensembl_rest.HTTPError as e:
                if ntries > 0:
                    self.logger.info("Server refused, trying again..." +
                                     ntries)
                    spids = (spids, ntries - 1)
                    self.getVariations(spids)
                else:
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

            try:
                for spid in spids:
                    self.varsdic[spid] = ensembl_rest.overlap_id(spid,
                                                                 params=optional)
                    vars = self.varsdic[spid]
                    self.varsdic[spid] = list(filter(lambda var:
                                                     var['consequence_type'] !=
                                                     filtvalue, vars))
                    self.logger.info(spid)
            except ensembl_rest.HTTPError as e:
                self.logger.exception(str(e))

    @ExceptionLogger("logger", KeyError, hlr.ch, "_loggermsg")
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

    @ExceptionLogger("logger", ValueError, hlr.ch, "_loggermsg")
    def assignExons(self, junctions):
        """
        Takes retrieved exonboundaries file and creates dictionaries
        of exon positions and names
        """

        exonpos = self._exonposdic
        exonname = self._exonnamedic
        pos = []
        ename = []

        # Skip header in file

        next(junctions)

        for count, row in enumerate(junctions):
            target = row[0]
            residue = row[2]
            isutr = row[9]
            name = 'exon' + str(count)

            if (isutr == 'true'):
                name = '5UTR'

            pos.append(residue)
            ename.append(name)
            exonpos[target] = pos
            exonname[target] = ename

            if len(pos) > 1:
                pos = []
                ename = []

        self._exonposdic = exonpos
        self._exonnamedic = exonname

    @ExceptionLogger("logger", ValueError, hlr.ch, "_loggermsg")
    def assignSNPs(self, variations):
        """
        Takes retrieved variations file and creates SNP
        dictionary
        """

        snpdic = self._snpdic

        # Skip header in file

        next(variations)

        for row in variations:
            target = row[0]
            residue = row[2]
            snpid = row[9]
            allele = row[10]
            if not(target in snpdic.keys()):
                snpdic[target] = {}
            snpdic[target][residue] = snpid + '({} {})'.format(residue,
                                                               allele)
        self._snpdic = snpdic

    @ExceptionLogger("logger", IndexError, hlr.ch, "_loggermsg")
    def extractTransfromCsvHeader(self, header, filtch):
        """
        Gets the transcript names given the header from oligout file
        """

        indexes = [sub.find(filtch) for sub in header]
        trans = [sub[:i] for sub, i in zip(header, indexes)]
        return trans

    @ExceptionLogger("logger", ValueError, hlr.ch, "_loggermsg")
    def createOligoOut(self, fname, oligout):
        """
        Merges variation, exon and oligo data together into final out file
        """

        all = []
        snpdic = self._snpdic
        exonnamedic = self._exonnamedic
        exonposdic = self._exonposdic

        # Get original header in file

        row = next(oligout)

        # Just take the transcript names from header

        starttrans = 8  # Index in header where transcripts start (Hardcoded)

        transcripts = row[starttrans:]
        transcripts = self.extractTransfromCsvHeader(transcripts, '_')
        transcripts = utils.noDuplicates(transcripts)

        starttrans -= 1

        # Modify file header

        row.append('transcriptLocation')

        for tran in transcripts:
            row.append(tran + '_snp')
        all.append(row)

        for count, row in enumerate(oligout):
            target = row[7]
            start = int(row[1])
            oligolen = int(row[3])
            added = False
            for index, name in enumerate(exonnamedic[target]):
                pos = exonposdic[target]
                pos = int(pos[index])
                if pos >= start:
                    row.append(name)
                    added = True
                    break
            if not(added):
                row.append('3UTR')

            # Add the snpids if they're within the interval

            for index, tran in enumerate(transcripts, start=1):
                index = starttrans + 2 * index  # Map to header index
                transtart = row[index]
                snips = []
                if transtart != 'NA':
                    transtart = transtart.split(' ')
                    transtart = [int(st) for st in transtart]
                    if tran in snpdic.keys():
                        for pos in snpdic[tran]:
                            if pos in snpdic[target].keys():
                                for tstart in transtart:
                                    transend = tstart + oligolen
                                    posint = int(pos)
                                    if tstart <= posint < transend:
                                        snips.append(snpdic[target][pos])
                row.append(' '.join(snips))
            all.append(row)

        # Write final set of rows to file

        with open(fname, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',
                                quotechar='', quoting=csv.QUOTE_NONE)
            writer.writerows(all)

    def createFastaFile(self, fname):
        """
        Outputs sequence dictionary into FASTA format
        """

        msg = []
        seqdic = self.seqsdic
        transcriptdic = self.transcriptdic
        maxcols = 60  # hardcoded

        for spec in self.allspecies:
            for tid in transcriptdic[spec]:
                msg.append('>{}'.format(tid))

                # Limit lines to maxcols

                string = textwrap.wrap(seqdic[tid], maxcols)
                for sub in string:
                    msg.append('{}'.format(sub))

        msg = '\n'.join(msg)
        outhandler = open(fname, 'w')
        outhandler.write(msg)
        outhandler.close()

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

    def prepareBoundaryData(self, trans):
        """
        Flattens boundary data structures into a matrix
        for csv format
        """

        matrixdata = []

        # Optimize this...

        for tran in trans:
            utrs = self.utrdic[tran]
            fivedis = self.getSeqObjCumuLength(utrs, 'five_prime_UTR')
            threedis = self.getSeqObjCumuLength(utrs, 'three_prime_UTR')
            exondis = len(self.seqsdic[tran]) - threedis
            fiveutrexists = fivedis > 0
            nfiveutrexists = str(not(fiveutrexists)).lower()
            fiveutrexists = str(fiveutrexists).lower()
            exonsexist = exondis > 0
            nexonexists = str(not(exonsexist)).lower()
            exonsexist = str(exonsexist).lower()
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

    def prepareVariationData(self, trans):
        """
        Flattens variation data structures into a matrix
        for csv format
        """

        matrixdata = []
        varsdic = self.varsdic
        genMapper = self.setGen2CdnaMap
        mapper = self.mapGen2Cdna

        # Optimize this...

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
