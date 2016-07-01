#!/usr/bin/env python

import sys, os

DIR = sys.argv[1]
OUT_FILE = 'condensed_results'

if __name__ == '__main__':
    header = [
        '|    Kernel | Class | NProcs |        Run-time |        MOp/s     |',
        '|-----------|-------|--------|-----------------|------------------|'
    ]
    data = []
    files = [f for f in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, f))]

    for f in files:
        test_attrs = f.split('.')
        benchmark = test_attrs[0]
        cls = test_attrs[1]
        nprocs = test_attrs[2]

        with open(os.path.join(DIR, f), 'r') as content:
            time_chunk = content.read().split('Time in seconds =')[1].strip()
            mops_chunk = time_chunk.split('Mop/s total     =')[1].strip()
            time = time_chunk.split()[0]
            mops = mops_chunk.split()[0]

        data.append("| %9s | %5s | %6s | %15s | %16s |" %
                    (benchmark, cls, nprocs, time, mops))

    data.sort()
    with open(OUT_FILE, 'a') as out:
        out.write('\n'.join(header + data))
