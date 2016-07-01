#!/usr/bin/env python

import argparse
import os
import sys
import time

from subprocess import check_output, STDOUT

NAS_BIN_DIR = '/shared/baremetal/NPB3.3.1/NPB3.3-MPI/bin'
NET_INTF = 'p10p1'
MPIHOSTS = 'mpihosts'
ALL_CLASSES = ['S', 'W', 'A', 'B', 'C', 'D', 'E', 'F']
NPROC_LIST = [8, 9, 16, 25, 32, 36, 49, 64, 81, 100, 121, 128, 144]
TIMESTAMP_FMT = "%d %b %Y %H:%M"
RANK_STRATEGIES = ['bind-host_split', 'bind-host_interleave', 'bind-host_fill_n']
SLOTS_PER_HOST = 2
CORES_PER_SLOT = 8

CORES_PER_HOST = SLOTS_PER_HOST * CORES_PER_SLOT

def check_pow_of_two(n):
    return ((n & (n-1)) == 0) and n != 0

def check_any(n):
    return True

def check_n_squared(n):
    l = [4, 9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225]
    if n > l[-1:][0]:
        return False
    return n in l

def build_rank_file(strategy, nprocs, hosts, filename, n=CORES_PER_HOST):
    num_hosts = len(hosts)
    nodes_per_host = nprocs/num_hosts
    contents = []

    if strategy == 'bind-host_split':
        for i in range(num_hosts - 1):

            contents += ['rank %d=%s slot=0:0-7,1:0-7' % (nodes_per_host * i + j, hosts[i])
                        for j in range(nodes_per_host)]

        contents += ['rank %d=%s slot=0:0-7,1:0-7' % (nodes_per_host * (num_hosts - 1) + j,
                     hosts[num_hosts - 1]) for j in range(nodes_per_host + (nprocs % num_hosts))]

    if strategy == 'bind-host_fill_n':
        pairs = []
        start = 0
        while start < nprocs:
            pairs += [(i, (i/n) % num_hosts) for i in range(start, start+n)]
            start += n
        pairs = filter(lambda x: x[0] < nprocs, pairs)
        contents += ['rank %d=%s slot=0:0-7,1:0-7' % (pair[0], hosts[pair[1]])
                    for pair in pairs]

    if strategy == 'rank-map-to-core':
        for i in range(num_hosts):
            for j in range(SLOTS_PER_HOST):
                for k in range(CORES_PER_SLOT):
                    rank = i*CORES_PER_HOST + j*CORES_PER_SLOT + k
                    if rank == nprocs:
                        break
                    args = (rank, hosts[i], j, k)
                    contents += ['rank %d=%s slot=%d:%d' % args]
                if rank == nprocs:
                    break
            if rank == nprocs:
                break    

    with open(filename, 'w') as f:
        f.write('\n'.join(contents))

ALL_BENCHMARKS = {
    'is': {'nprocs_constraint': check_pow_of_two},
    'ep': {'nprocs_constraint': check_any},
    'cg': {'nprocs_constraint': check_pow_of_two},
    'mg': {'nprocs_constraint': check_pow_of_two},
    'ft': {'nprocs_constraint': check_pow_of_two},
    'bt': {'nprocs_constraint': check_n_squared},
    'sp': {'nprocs_constraint': check_n_squared},
    'lu': {'nprocs_constraint': check_n_squared}
}

def arg_list(s):
    if s[0] == ',':
        s = s[1:]
    if s[-1:] == ',':
        s = s[:-1]

    return s.split(',')

def num_range(s):
    result = s.split('-')
    if len(result) != 2:
        return None
    if int(result[0]) < int(result[1]):
        return (int(result[0]), int(result[1])+1)
    else:
        return (int(result[1]), int(result[0])+1)

def nprocs_valid(nprocs, benchmark):
    return ALL_BENCHMARKS[benchmark]['nprocs_constraint'](nprocs)

def launch_benchmark(benchmark, benchmark_class, host_file, nprocs, bin_dir,
                     output_file, rank_file=None, net_intf=None):

    launch_args = ['mpirun', '-hostfile', host_file, '-np', str(nprocs)]
    if net_intf:
        launch_args += ['--mca', 'btl_tcp_if_include', net_intf]
    if rank_file:
        #launch_args += ['--mca', 'rmaps_rank_file_path', rank_file]
        launch_args += ['--rankfile', rank_file]
        with open(rank_file, 'r') as f:
            rank_file_contents = f.read()
    #launch_args += ['-mca', 'btl', 'tcp,self']
    launch_args += ['--bind-to', 'core', '--map-by', 'core']
    launch_args += ['--report-bindings']

    launch_args.append('%s/%s.%s.%s'
                       % (bin_dir, benchmark, benchmark_class, nprocs))

    print 'Running:\n%s' % ' '.join(launch_args)
    timestamp = time.strftime(TIMESTAMP_FMT)
    output = check_output(launch_args, stderr=STDOUT)

    with open(host_file, 'r') as f:
        host_file_contents = f.read()

    with open(output_file, 'w') as f:
        f.write(timestamp)
        f.write('\n\n######### LAUNCH COMMAND:\n\n')
        f.write(' '.join(launch_args))
        f.write('\n\n######### JOB OUTPUT:\n\n')
        f.write(output)
        f.write('\n\n######### HOSTFILE (%s) CONTENTS:\n\n' % host_file)
        f.write(host_file_contents)
        if rank_file:
            f.write('\n\n######### RANKFILE (%s) CONTENTS:\n\n' % rank_file)
            f.write(rank_file_contents)

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('hostfile')
    arg_parser.add_argument('--classes', type=arg_list)
    arg_parser.add_argument('--nprocs', type=int)
    arg_parser.add_argument('--nprocs_range', type=num_range)
    arg_parser.add_argument('--benchmarks', type=arg_list)
    arg_parser.add_argument('--rank_strategy')
    args = arg_parser.parse_args(sys.argv[1:])

    nprocs = args.nprocs
    hostfile = args.hostfile

    if args.classes:
        classes = args.classes
    else:
        classes = ALL_CLASSES

    if args.benchmarks:
        benchmarks = args.benchmarks
    else:
        benchmarks = ALL_BENCHMARKS.keys()

    if args.nprocs_range:
        nprocs_range = args.nprocs_range
    elif args.nprocs:
        nprocs_range = (args.nprocs, args.nprocs + 1)
    else:
        nprocs_range = (NPROC_LIST[0], NPROC_LIST[-1:][0]+1)

    if args.rank_strategy:
        rank_strategy = args.rank_strategy
    else:
        rank_strategy = None

    with open(hostfile, 'r') as f:
        host_lines = f.read().split('\n')
    if host_lines[len(host_lines)-1] == '':
        host_lines = host_lines[:-1]

    hosts = map(lambda x: x.split()[0], host_lines)

    for cls in classes:
        for benchmark in benchmarks:
            nprocs_list = [n for n in NPROC_LIST if (n in range(*nprocs_range)
                           and nprocs_valid(n, benchmark))]
            for nprocs in nprocs_list:
                if rank_strategy:
                    build_rank_file(rank_strategy, nprocs, hosts, 'rankfile')
                    launch_benchmark(benchmark, cls, hostfile, nprocs,
                                     NAS_BIN_DIR,
                                     '%s.%s.%d.results' % (benchmark, cls, nprocs),
                                     'rankfile', NET_INTF)
                else:
                    launch_benchmark(benchmark, cls, hostfile, nprocs,
                                     NAS_BIN_DIR,
                                     '%s.%s.%d.results' % (benchmark, cls, nprocs),
                                     net_intf=NET_INTF)

    #os.remove('rankfile')
