#!src/env/bin/python

import argparse
import paramiko
import os
import sys
from configobj import ConfigObj

SRC_DIR = 'src'
IMG_DIR = os.path.join(SRC_DIR, 'img')

def launch_host(hostname, username, image, build, network, nodes, node_prefix):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username)

    if build:
        build_args = ['docker', 'build', '-t', image, IMG_DIR]
        build_command = 'echo %s' % ('"' + ' '.join(build_args) + '"')
        stdin, stdout, stderr = ssh.exec_command(build_command)
        print 'stdout: ', stdout.readlines()
        print 'stderr: ', stderr.readlines()

    for node in nodes:
        print 'Launching node %s on host %s' % (node, hostname)

        node_name = node_prefix + node
        launch_args = ['docker', 'run', '--name=%s' % node_name,
                       '--hostname=%s' % node_name, '-d',
                       '--net=%s' % network,
                       image, '/usr/sbin/sshd', '-D']
        launch_command = 'echo %s' % ('"' + ' '.join(launch_args) + '"')
        stdin, stdout, stderr = ssh.exec_command(launch_command)
        print 'stdout: ', stdout.readlines()
        print 'stderr: ', stderr.readlines()

    ssh.close()

def launch_head_node(head_name, image, network):
    args = ['docker', 'run', '--name=%s' % head_name,
            '--hostname=%s' % head_name, '-i', '-t', '--rm=true',
            '--net=%s' % network, image, '/bin/bash', '-l']
    print ' '.join(args)
    #ret = call(args) 

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                prog='launch.py',
                description='Launch a container-based virtual cluster.'
             )

    parser.add_argument('--cfg', help='Virtual cluster config filename.')
    parser.add_argument('--build', action='store_true',
                        help='Build image on all hosts prior to launching.')
    args = parser.parse_args()
    cfg = ConfigObj(args.cfg)
    print cfg

    for host in cfg['hosts']:
        launch_host(
            host,
            cfg['hosts'][host]['username'],
            cfg['image'],
            args.build,
            cfg['network'],
            cfg['hosts'][host]['nodes'],
            cfg['node_name_prefix']
        )

    launch_head_node(cfg['head_name'], cfg['image'], cfg['network'])

