#! /usr/bin/env python3

import re
import time
import requests
import logging
import textwrap
import subprocess
import csv
import multiprocessing
import simplejson.errors
import utilitiesservice as utils
import projectloghandler as hlr
from itertools import islice
from multiprocessing import Pool
from exceptionlogger import ExceptionLogger


def logHandler(fname, logfile=False):
    hlr.logHandler(file=logfile, filename=fname)


class BowtieService:
    def __init__(self, fastafiles):
        self.logger = ExceptionLogger.create_logger(hlr.ch, logging.INFO,
                                                    __name__)
        self._loggermsg = ''
        self._bowtie = 'BOWTIE'
        self._indexes = 'BOWTIE_INDEXES'
        self._build = 'BOWTIE_BUILD'
        self._basename = 'onTarget' + str(utils.pid())
        self._infilename = '.dnaOligo.fa'
        self._multprocsinfile = False
        self.tmpdir = '/tmp/'
        self.file = ''
        self.reader = ''
        self.mismatch = 2
        self.outfilename = ""
        self.inputvars = []
        self.checkBowtie()
        self.getBowtieEnvs()
        if fastafiles:
            self.buildIndex(fastafiles)

    def checkBowtie(self):
        """
        Checks bowties existence in system
        """
        utils.which('bowtie')

    @ExceptionLogger('logger', TypeError, hlr.ch, '_loggermsg')
    def prepareInput(self, primaryid, enumoligos):
        self._infilename = primaryid + self._infilename
        fname = self._infilename
        msg = []

        for count, oligo in enumerate(enumoligos[0], start=1):
            msg.append('>{}_{}'.format(primaryid, count))
            msg.append('{}'.format(oligo))

        msg = '\n'.join(msg)
        outhandler = open(fname, 'w')
        outhandler.write(msg)
        outhandler.close()

    def getBowtieEnvs(self):
        """
        Prepare all Bowties env variables
        """
        vars = utils.env([self._bowtie,
                          self._indexes,
                          self._build])
        self._bowtie = vars[0]
        self._indexes = vars[1]
        self._build = vars[2]

    def createIndexes(self, fileset):
        """
        Wrapper that calls the Index building function
        given a dictionary in the form filename, fasta
        """
        filename, fasta = fileset
        self.buildIndex(fasta, filename)

    def getSeqs(self, spids, ntries):
        """
        This method was written adHoc based on the behavior
        of multiple requests in the ENSEMBL REST API. It
        is highly recommended to download and Install a local
        copy of the REST API due to the high intermittency in
        its website. Server is hardcoded to ensembl rest website
        """
        seqsdic = {}
        if isinstance(spids, str):
            spids = [spids]

        server = "https://rest.ensembl.org"

        # This is for local ensembl RESTful VM

        # server = "http://127.0.0.1:3000"
        ext = "/sequence/id"
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json",
                   "Cache-Control": "no-cache",
                   "Pragma": "no-cache"}

        sids = ['"' + x + '"' for x in spids]
        sids = (', ').join(sids)
        sids = '[{}]'.format(sids)
        sids = '{ "ids" : ' + sids + ' }'
        r = requests.post(server+ext, headers=headers,
                          data=sids)

        if r.status_code == 503:
            if ntries > 0:
                self.logger.info('Server refused with code 503 for transcripts {}, retrying {}...'.format(spids[0], ntries))
                time.sleep(3)
                self.getSeqs(spids, ntries - 1)
            else:
                self.logger.error('Failed to retrieve info from server, exiting')
                r.raise_for_status
        elif not r.ok:
            r.raise_for_status
            raise ValueError
        else:
            try:
                decoded = r.json()
                if not decoded:
                    if ntries > 0:
                        self.logger.info('Empty file was returned for transcripts {}, retrying {}...'.format(spids[0], ntries))
                        time.sleep(3)
                        self.getSeqs(spids, ntries - 1)
                else:
                    for idx, info in enumerate(decoded):
                        seqsdic[info['id']] = info['seq']
                        if not info:
                            self.logger.info('There is an empty file for transcripts {}, retrying {}...'.format(spids[idx], ntries))
                            if ntries > 0:
                                time.sleep(3)
                                self.getSeqs(spids, ntries - 1)
                    return seqsdic
            except simplejson.errors.JSONDecodeError as e:
                if ntries > 0:
                    self.logger.info('There was an error writing back from server for transcripts {}, retrying {}...'.format(spids[0], ntries))
                    time.sleep(3)
                    self.getSeqs(spids, ntries - 1)
                else:
                    self.logger.exception(str(e))
                    raise e

    def writeSeqs(self, trans):
        """
        Gets Sequences from ENSEMBL and streams them into a FASTA file
        """
        regularnamedic = {'ENSMUST': 'Mouse',
                          'ENSRNOT': 'Rat',
                          'ENST': 'Human',
                          'ENSCAFT': 'Dog',
                          'ENSPTRT': 'Chimp',
                          'ENSMMUT': 'Macaca'}

        maxcols = 60  # hardcoded
        maxpostcalls = 50
        tmpdir = self.tmpdir

        try:
            fname = re.split('(\d+)', trans[0])
            fname = fname[0]
            fname = 'all' + regularnamedic[fname] + 'UnsplicedGene.v55.fa'
            if self._multprocsinfile:
                fname = fname + str(multiprocessing.current_process().pid)
            seqsfun = self.getSeqs
            tot = len(trans)
            outf = open(tmpdir + fname, 'w')
            trans = [tran.split('.')[0] for tran in trans]
            self.logger.info('Attempting to write file {}...'.format(fname))

            for idx in range(0, tot, maxpostcalls):
                seqdic = {}
                ntries = 10
                endx = idx + maxpostcalls
                while ntries > 0 and not seqdic:
                    seqdic = seqsfun(trans[idx:endx], ntries)
                    if not seqdic:
                        self.logger.info('Empty dictionary for {}, retrying {}...'.format(trans[idx], ntries))
                        ntries = ntries - 1
                for tid in trans[idx:endx]:
                    outf.write('>' + tid + '\n')
                    string = textwrap.wrap(seqdic[tid], maxcols)
                    for sub in string:
                        outf.write(sub)
                    outf.write('\n')

            self.logger.info('File {} written!'.format(fname))
            outf.close()
        except ValueError as e:
            self.logger.exception(str(e))

    @ExceptionLogger('logger', ValueError, hlr.ch, '_loggermsg')
    def createUnsplicedIndexesfromCDNAFasta(self, fasta, nthreads, idsfun,
                                            unspliced=True, mworkers=False):
        """
        Extracts each transcript from given fasta file and queries ENSEMBL
        for sequences in order to build indexes
        """
        regularnamedic = {'Mus_musculus': 'Mouse',
                          'Rattus_norvegicus': 'Rat',
                          'Homo_sapiens': 'Human',
                          'Canis_familiaris': 'Dog',
                          'Pan_troglodytes': 'Chimp',
                          'Macaca_mulatta': 'Macaca'}

        if mworkers:
            nthreadsx = nthreads
            self._multprocsinfile = True
            tot = len(fasta)
            nthreads = 1
        else:
            tot = int(len(fasta) / nthreads)

        if unspliced:
            # Get all transcript IDs
            for count in range(tot):
                self.logger.info(fasta)
                with Pool(nthreads) as p:
                    trans = p.map(idsfun, fasta)

            # Query ENSEMBL for all sequences for all IDs and create fasta file

            if mworkers:
                nthreads = nthreadsx
                tot = int(len(trans[0]) / nthreads)
                trans = iter(trans[0])
                length = [tot for i in range(nthreads)]
                trans = [list(islice(trans, elem))
                         for elem in length]

            for count in range(tot):
                with Pool(nthreads) as p:
                    p.map(self.writeSeqs, trans)

        # Build Indexes

        files = [file.split('.')[0] for file in fasta]
        path = files[0].split('/')[:-1]
        path = ('/').join(path)
        files = [file.split('/')[-1] for file in files]
        files = ['all' + regularnamedic[file] +
                 'UnsplicedGene.v55' for file in files]

        inputs = [(file, path + '/' + file + '.fa') for file in files]

        # Combine files if needed

        if mworkers:
            inputs = inputs[0]
            subprocess.call('cat ' + inputs + '*' + '> ' + inputs)

        self.logger.info('Attempting to Build indexes...')

        for count in range(tot):
            with Pool(nthreads) as p:
                p.map(self.createIndexes, inputs)

    @ExceptionLogger('logger', KeyError, hlr.ch, '_loggermsg')
    def buildBowtieIndexesfromEnsemblGenomicSeq(self, typeseq, species, idsfun,
                                                nthreads=1,
                                                indexdir=None, tmpdir='/tmp/',
                                                download=True,
                                                unspliced=True,
                                                mworkers=False,
                                                fun='', ntries=2):
        """
        Get type genomic sequences directly from the ENSEMBL ftp site and
        use bowtie to create all the indexes from this sequences
        """

        # TODO: gunzip and gz are the only recognizable decompressor
        # and format, change to a dictionary of decompressor and fomats

        typeseqdic = {'cdna': 'all',
                      'dna': 'toplevel'}

        specdbdic = {'Mus_musculus': 'GRCm38',
                     'Rattus_norvegicus': 'Rnor_6.0',
                     'Homo_sapiens': 'GRCh38',
                     'Canis_familiaris': 'CanFam3.1',
                     'Pan_troglodytes': 'Pan_tro_3.0',
                     'Macaca_mulatta': 'Mmul_10'}

        regularnamedic = {'Mus_musculus': 'Mouse',
                          'Rattus_norvegicus': 'Rat',
                          'Homo_sapiens': 'Human',
                          'Canis_familiaris': 'Dog',
                          'Pan_troglodytes': 'Chimp',
                          'Macaca_mulatta': 'Macaca'}

        if indexdir is None:
            indexdir = self._indexes

        # Set everything in the right format (e.g Homo_sapiens, cdna)

        if not(isinstance(species, list)):
            species = [species]
        if not(isinstance(typeseq, list)):
            typeseq = [typeseq]

        self.tmpdir = tmpdir

        Species = [sp.capitalize() for sp in species]
        typeseq = [ty.lower() for ty in typeseq]

        files = [('.').join([sp, specdbdic[sp],
                             tseq,
                             typeseqdic[tseq], 'fa', 'gz'])
                 for sp in Species for tseq in typeseq]
        self.logger.info(files)

        if mworkers:
            tot = int(len(files))
        else:
            tot = int(len(files) / nthreads)

        if download:
            ftpsite = 'ftp://ftp.ensembl.org/pub/release-98/fasta/'

            # Prepare urls to download on local file directories,
            # if decompressing function is given, add it

            stype = len(typeseq)

            urls = [(tmpdir + files[i + stype * j],
                     ftpsite + ('/').join([sp, tseq]) + '/' +
                     files[i + stype * j],
                     fun, ntries)
                    for i, tseq in enumerate(typeseq)
                    for j, sp in enumerate(species)]

            # Get seq files from ENSEMBL ftp site and decompress

            self.logger.info('Attempting to download files...')

            for count in range(tot):
                index = count * nthreads
                suburls = urls[index: index + nthreads]
                self.logger.info(suburls)
                utils.callParallelFetchUrl(suburls, nthreads)

        # Files have already been extracted

        files = [tmpdir + file.replace('.gz', '') for file in files]

        # Create FASTA files for each species unspliced
        # DNA using cDNA fasta

        self.createUnsplicedIndexesfromCDNAFasta(files, nthreads,
                                                 idsfun, unspliced,
                                                 mworkers)

        # Move to index directory TODO: Fill this in

        # Build Bowtie Indexes

        name = ['all' + regularnamedic[specie] + 'cDNA.v55'
                for specie in Species]

        inputs = [(file, ffile) for (file, ffile) in zip(name, files)]

        self.logger.info('Attempting to Build indexes...')

        if mworkers:
            nthreads = 1

        for count in range(tot):
            with Pool(nthreads) as p:
                p.map(self.createIndexes, inputs)

    def buildIndex(self, fastafiles, basename=''):
        """
        Groups basefiles and dumps bowtie build output
        """

        if not(basename):
            basename = self._basename

        if isinstance(fastafiles, str):
            basefiles = fastafiles
        else:
            basefiles = ','.join(fastafiles)

        prog = self._build
        args = [basefiles, basename]

        self.logger.info('Running {} {}'.format(prog, ' '.join(args)))
        utils.run(prog, args, fname=basename + 'dump')

    def search(self, btype='sense', mismatch=2, input='', basename=''):
        """
        Find alignments and report in outfile
        """

        if not(input):
            input = self._infilename

        if not(basename):
            basename = self._basename

        if not(0 <= mismatch <= 3):
            mismatch = 2

        mismatch = str(mismatch)

        options = ['-a', '--best']

        options = options + ['-v', mismatch]

        if btype == 'antisense':
            options = options + ['--nofw', '-f']
        else:
            options = options + ['--norc', '-f']

        self._outfilename = input + '_' + basename + '.out'
        outfile = self._outfilename
        noalign = input + '_' + basename + '.noAlign'

        options = options + ['--un', noalign, basename, input]

        prog = self._bowtie

        indexes = ['BOWTIE_INDEXES', self._indexes]

        self.logger.info('Running {} {}'.format('set', ' '.join(indexes)))
        utils.osset(' '.join(indexes))

        self.logger.info('Running {} {}'.format(prog, ' '.join(options)))
        utils.run(prog, options, fname=outfile)

        self._outfilename = outfile
        return outfile

    def parseOutput(self, outf=None):
        """
        Retrieve components from Bowties output and create data structure
        """

        if outf is None:
            outf = self._outfilename

        self.file = open(outf)
        self.reader = csv.reader(self.file, delimiter='\t')
        return self.reader

    def resetMatchDis(self, transcripts, transdic, target):
        for tran in transcripts:
            transdic[tran] = {}
            transdic[tran]['match'] = '>2'
            transdic[tran]['pos'] = 'NA'
        transdic[target]['match'] = '0'

    def writeMatchDis2Line(self, transcripts, writer, oligos,
                           transdic, target, oligolen, index, count):
        line = [index, count, count + oligolen - 1,
                oligolen, oligos[0][count - 1], oligos[1][count - 1],
                oligos[2][count - 1], target]

        for tran in transcripts:
            match = transdic[tran]['match']
            pos = transdic[tran]['pos']
            if isinstance(match, list):
                match = ' '.join(match)
                pos = ' '.join(pos)
            line.append(match)
            line.append(pos)

        writer.writerow(line)

    @ExceptionLogger("logger", KeyError, hlr.ch, "_loggermsg")
    def writeOligoOut(self, header, fname, transcripts,
                      oligos, oligolen, target, reader=None):
        """
        Gets output from bowtie search and modifies reader for oligos
        """

        if reader is None:
            reader = self.reader

        count = 1
        transdic = {}
        resetMatchDis = self.resetMatchDis
        writeMatchDis2Line = self.writeMatchDis2Line

        # Initialize the values for all transcripts

        self.logger.info(transcripts)

        resetMatchDis(transcripts, transdic, target)
        idaux = target + '_1'

        with open(fname, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',
                                quotechar='', quoting=csv.QUOTE_NONE)

            # Write header to file

            writer.writerow(header)

            # Operate on each line from bowtie-out and write to output

            for row in reader:
                id = row[0]
                trans = row[2]
                if not(trans in transcripts):
                    continue
                matchr = row[7]
                pos = int(row[3]) + 1

                # Write line and reset everything if name is different

                if id != idaux:
                    writeMatchDis2Line(transcripts, writer, oligos, transdic,
                                       target, oligolen, idaux, count)
                    resetMatchDis(transcripts, transdic, target)
                    count += 1

                if isinstance(transdic[trans]['pos'], list):
                    if trans == target and not(matchr):
                        transdic[target]['pos'] += [str(count)]
                    else:
                        transdic[trans]['pos'] += [str(pos)]
                    if matchr:
                        match = matchr.split(',')
                        match = str(len(match))
                        transdic[trans]['match'] += [match]
                    else:
                        transdic[trans]['match'] += ['0']
                else:
                    transdic[trans]['pos'] = [str(pos)]
                    if trans == target and not(matchr):
                        transdic[target]['pos'] = [str(count)]
                    if matchr:
                        match = matchr.split(',')
                        match = str(len(match))
                        transdic[trans]['match'] = [match]
                    else:
                        transdic[trans]['match'] = ['0']

                idaux = id

            # Write last line

            writeMatchDis2Line(transcripts, writer, oligos, transdic,
                               target, oligolen, idaux, count)
            resetMatchDis(transcripts, transdic, target)
        csvfile.close()

    def cleanUp(self):
        """
        Remove all ebwt files form working directory
        """

        self.file.close()
        utils.rm('*.ebwt')
