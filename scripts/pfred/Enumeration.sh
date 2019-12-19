#! /bin/bash

set -euxo pipefail

[ -f paco.txt ] && rm paco.txt

RunDesign.py getSeqTranscripts -l "$1" -f sequence.fa -a exonBoundaries.csv -v variationData.csv
RunDesign.py callBowtieEnumerate -p "$2" -l "$3" -f sequence.fa -o oligoOut.csv
RunDesign.py joinOligoOut -l oligoOut.csv -j exonBoundaries.csv -v variationData.csv -o outputSummary_.csv

cat outputSummary_.csv | awk -F"," '{print ","$1}' | sed -e 's/name/oligoName/g'> name.txt
paste -d'\0' outputSummary_.csv name.txt > EnumerationResult.csv

echo "paco" > paco.txt
