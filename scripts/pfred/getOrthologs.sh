#! /bin/bash
echo "runing getEnsemblOrthologTranscripts.pl"
RunDesign.py getOrthologs -g "$1 " -s "$2" -l "$3" -o seqAnnotation.csv;
echo "runing getEnsemblOrthologTranscripts.py ... done"

