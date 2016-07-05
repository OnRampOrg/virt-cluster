#!src/env/bin/python

import argparse
import paramiko
import os
import sys
from configobj import ConfigObj
from subprocess import call

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

def launch_network(net_name, subnet):
    args = ['docker', 'network', 'create', '--driver=overlay',
            '--subnet=%s' % subnet, net_name]
    print ' '.join(args)
    #ret = call(args) 

def setup_root_dir(root_dir):
    ssh_dir = os.path.join(root_dir, '.ssh')
    call(['mkdir', '-p', ssh_dir])
    call(['chmod', '700', ssh_dir])
    call(['ssh-keygen', '-f', os.path.join(ssh_dir, 'id_rsa'), '-t', 'rsa',
          '-N', ''])
    call(['cp', os.path.join(ssh_dir, 'id_rsa.pub'),
          os.path.join(ssh_dir, 'authorized_keys')])
    call(['chmod', '700', os.path.join(ssh_dir, 'authorized_keys')])
    with open(os.path.join(ssh_dir, 'config'), 'w') as f:
        f.write('Host *\n    StrictHostKeyChecking no')
    if os.path.exists(os.path.join(ssh_dir, 'known_hosts')):
        os.path.remove(os.path.join(ssh_dir, 'known_hosts'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                prog='launch.py',
                description='Launch a container-based virtual cluster.'
             )

    parser.add_argument('CFG_FILENAME', help='Virtual cluster config filename.')
    parser.add_argument('--all', action='store_true',
                        help='Same as: --build --net --setup-root-dir.')
    parser.add_argument('--build', action='store_true',
                        help='Build image on all hosts prior to launching.')
    parser.add_argument('--net', action='store_true',
                        help='Launch the cluster overlay network.')
    parser.add_argument('--rootdir', action='store_true',
                        help=('Prepare the shared root folder with ssh keys, '
                              'hostfiles, rankfiles, etc.'))
    args = parser.parse_args()

    cfg = ConfigObj(args.CFG_FILENAME)
    print cfg

    if args.rootdir or args.all:
        setup_root_dir(cfg['root_folder'])

    if args.net or args.all:
        launch_network(cfg['network'], cfg['subnet'])

    for host in cfg['hosts']:
        launch_host(
            host,
            cfg['hosts'][host]['username'],
            cfg['image'],
            args.build or args.all,
            cfg['network'],
            cfg['hosts'][host]['nodes'],
            cfg['node_name_prefix']
        )

    launch_head_node(cfg['head_name'], cfg['image'], cfg['network'])

