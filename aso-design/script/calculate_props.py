#!/usr/bin/env python

import sys
from Bio.SeqUtils import molecular_weight
from Bio.SeqUtils import MeltingTemp as mt

print("python: " + sys.version, end="\n", file=sys.stderr)
print(sys.argv[1], end="\n", file=sys.stderr)

with open(sys.argv[1]) as file:
    for line in file:
        row = line.rstrip('\n').split("\t")
        seq = row[3]

        if seq == 'cdna':
            row.extend(["tm_nn", "tm_gc", "tm_wallace"])
            print(",".join(row))

        else:
            mw = molecular_weight(seq, 'DNA', False)

            row.append('%0.2f' % mt.Tm_NN(seq))
            row.append('%0.2f' % mt.Tm_GC(seq))
            row.append('%0.2f' % mt.Tm_Wallace(seq))

            print(",".join(row))
