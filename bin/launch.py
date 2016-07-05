#!src/env/bin/python

import argparse
import paramiko
import sys
from configobj import ConfigObj

def launch_host(hostname, username, image, network, nodes, node_prefix):
    for node in nodes:
        print 'Launching node %s on host %s' % (node, hostname)

        node_name = node_prefix + node
        args = ['docker', 'run', '--name=%s' % node_name,
                '--hostname=%s' % node_name, '-d',
                '--net=%s' % network,
                image, '/usr/sbin/sshd', '-D']

        command = 'echo %s' % ('"' + ' '.join(args) + '"')

        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username)
        stdin, stdout, stderr = ssh.exec_command(command)
        print 'stdout: ', stdout.readlines()
        print 'stderr: ', stderr.readlines()

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
    args = parser.parse_args()
    cfg = ConfigObj(args.cfg)
    print cfg

    for host in cfg['hosts']:
        launch_host(
            host,
            cfg['hosts'][host]['username'],
            cfg['image'],
            cfg['network'],
            cfg['hosts'][host]['nodes'],
            cfg['node_name_prefix']
        )

    launch_head_node(cfg['head_name'], cfg['image'], cfg['network'])

