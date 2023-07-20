#! /usr/bin/env python3

import sys
import unittest
from natsort import natsorted
import utilitiesservice as utils


class TestEnumeration(unittest.TestCase):
    """
    This is more of an integration test suite.
    Gets Gene ID, species of interest and target species
    from command line inputs. Runs the first half in Perl and then
    runs the other half in both Perl and Python in order to compare
    final outputs
    """

    geneid = 'ENSG00000165175'
    species = 'human'
    interestsp = 'rat,dog'
    oligolen = '14'

    def test_oligoout(self):
        # Run Shell scripts

        # Get orthologs

        prog = 'getEnsemblOrthologTranscripts.pl'
        geneid = self.geneid
        species = self.species
        interestsp = self.interestsp
        outf = 'seqAnnotation.csv'
        options = ['-g', geneid, '-s', species, '-l', interestsp, '-o', outf]
        utils.run(prog, options)

        # Get transcripts

        with open(outf) as f:
            transcripts = [row.split(',')[0] for row in f]

        trans = transcripts[1:]
        trans = (',').join(trans)

        # Get seqs

        prog = 'getSeqForTranscriptIds.pl'
        fastaf = 'sequence.fa'
        exonout = 'exonBoundaries.csv'
        varout = 'variationData.csv'

        options = ['-l', trans, '-f', fastaf, '-a', exonout, '-v', varout]
        utils.run(prog, options)

        # Run perl script

        prog = 'RnaEnumeration.pl'
        target = 'ENST00000378474'
        oligolen = self.oligolen
        outf = 'oligoOut.csv'
        options = ['-p', target, '-l', oligolen, '-f', fastaf, '-o', outf]
        utils.run(prog, options)

        # Final CSV file

        prog = 'joinOligoAnnotations.pl'
        oligout = outf
        outf = 'outputSummary_.csv'
        options = ['-l', oligout, '-j', exonout, '-v', varout, '-o', outf]
        utils.run(prog, options)

        # Now run the python analogous

        outfnew = 'new' + oligout
        options = ['-p', target, '-l', oligolen, '-f', fastaf, '-o', outfnew]
        options = ['callBowtieEnumerate'] + options
        prog = 'RunDesign.py'
        utils.run(prog, options)

        outfnewf = 'new' + outf
        options = ['-l', outfnew, '-j', exonout, '-v', varout, '-o', outfnewf]
        options = ['joinOligoOut'] + options
        utils.run(prog, options)

        # Get header from test files

        [filepl, readpearl] = utils.readAnnotationCsv(oligout)
        [filepy, readpython] = utils.readAnnotationCsv(outfnew)
        rowpl = next(readpearl)
        rowpy = next(readpython)

        # Extract indexes of equivalent elements in both headers

        indexesh = [rowpl.index(el) for el in rowpy]

        # Run the test

        self.assertEqual(len(indexesh), len(rowpl))

        for rowpl, rowpy in zip(readpearl, readpython):
            values = [rowpl[el] for el in indexesh]
            self.assertListEqual(values, rowpy)

        # Flush out

        filepl.close()
        filepy.close()

        # Get header from test files

        [filepl, readpearl] = utils.readAnnotationCsv(outf)
        [filepy, readpython] = utils.readAnnotationCsv(outfnewf)
        rowpl = next(readpearl)
        rowpy = next(readpython)

        # Extract indexes of equivalent elements in both headers

        indexesh = [rowpl.index(el) for el in rowpy]

        # Run the test

        self.assertEqual(len(indexesh), len(rowpl))

        for rowpl, rowpy in zip(readpearl, readpython):
            values = [rowpl[el] for el in indexesh]
            for idx, (row, value) in enumerate(zip(rowpy, values)):
                if '(' in value:
                    value = value.split(') ')
                    value = natsorted(value, key=lambda y: y.lower())
                    values[idx] = (') ').join(value)
                if '(' in row:
                    row = row.split(') ')
                    row = natsorted(row, key=lambda y: y.lower())
                    rowpy[idx] = (') ').join(value)
            self.assertListEqual(values, rowpy)

        # Flush out

        filepl.close()
        filepy.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        TestEnumeration.oligolen = sys.argv.pop()
        TestEnumeration.interestsp = sys.argv.pop()
        TestEnumeration.species = sys.argv.pop()
        TestEnumeration.geneid = sys.argv.pop()
    unittest.main()
