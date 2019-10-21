#! /usr/bin/env python3

import logging
import csv
import utilitiesservice as utils
import projectloghandler as hlr
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
        self.file = ''
        self.reader = ''
        self.mismatch = 2
        self.outfilename = ""
        self.inputvars = []
        self.checkBowtie()
        self.getBowtieEnvs()
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

    def buildIndex(self, fastafiles):
        """
        Groups basefiles and dumps bowtie build output
        """

        if isinstance(fastafiles, str):
            basefiles = fastafiles
        else:
            basefiles = ','.join(fastafiles)

        prog = self._build
        args = [basefiles, self._basename]

        self.logger.info('Running {} {}'.format(prog, ' '.join(args)))
        utils.run(prog, args, fname='dump')

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
