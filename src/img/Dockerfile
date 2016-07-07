FROM ubuntu
MAINTAINER OnRampOrg

# System setup
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive \
    apt-get install -y openssh-server openssl libssl-dev build-essential \
                       gfortran libgfortran3 vim

# OpenMPI
RUN wget https://www.open-mpi.org/software/ompi/v1.10/downloads/openmpi-1.10.3.tar.bz2
RUN tar -xf openmpi-1.10.3.tar.bz2
RUN cd openmpi-1.10.3 && ./configure --prefix=/usr/local && make && make install

# SSH
ENV HOME /root
RUN mkdir /var/run/sshd
RUN ssh-keygen -A

EXPOSE 22
