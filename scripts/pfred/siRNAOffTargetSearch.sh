#! /bin/bash
#echo "line1"
#source env.sh
#echo "line2"
#echo "run input test.txt"

# Flag file paco in case client gets 504 error

[ -f paco.txt ] && rm paco.txt

cat EnumerationResult.csv | cut -f 1,5 -d ','>foo.csv
sed '1d' foo.csv |tr ',' '\t'> test.txt

IFILE="test.txt"
cat $IFILE
species="human"
targetGene="ENSG00000113580"
type="sense"
mismatch="2"
OFILE="siRNAOffTarget.out"

siRNA_OffTargetSearch_bowtie.pl  -s "$1" -g "$2" -t $type  -v "$3" $IFILE > $OFILE

# Check if script was successful
if [ $? -eq 0 ]; then
    echo OK
else
    echo "Off Target search pl, failed!"
    exit 1
fi

echo "result"
head $OFILE

cp EnumerationResult.csv outputSummaryBeforeMerge.csv
cat outputSummaryBeforeMerge.csv|tr ',' '\t' |mergeEx.pl 1 1 siRNAOffTarget.out keepAll 1|tr '\t' ','>siRNAOffTargetSearchResult.csv

echo "paco" > paco.txt
