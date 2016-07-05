#!/usr/bin/env python

import os
import shutil
import sys
from subprocess import call

PROJ_NAME = 'virt-cluster'
SRC_DIR = 'src'
ENV_DIR = os.path.join(SRC_DIR, 'env')

if os.path.exists(ENV_DIR):
    print '%s appears to be already installed.' % PROJ_NAME
    response = raw_input('(R)emove and re-install or (A)bort? ')
    if response != 'R' and response != 'r':
        sys.exit('Aborted')
    else:
        shutil.rmtree(ENV_DIR)

call(['virtualenv', '-p', 'python2.7', ENV_DIR])
call([ENV_DIR + '/bin/pip', 'install', '-r', SRC_DIR + '/requirements.txt'])
