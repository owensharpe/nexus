FROM ubuntu:20.04

# forego timezone configuration
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /sw

RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get -y install build-essential \
        zlib1g-dev \
        libncurses5-dev \
        libgdbm-dev \
        libnss3-dev \
        libssl-dev \
        libreadline-dev \
        libffi-dev \
        libsqlite3-dev \
        libbz2-dev \
        curl \
        wget \
        libpq-dev \
        g++ \
        git \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        liblzma-dev \
        lzma \
        libblas3 \
        liblapack3 \
        liblapack-dev \
        libblas-dev \
        gfortran \
        pkg-config \
        unzip

RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt update -y
RUN apt -y install python3.10 python3.10-dev
RUN apt-get purge -y imagemagick imagemagick-6-common
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

RUN curl -fsSL https://debian.neo4j.com/neotechnology.gpg.key | apt-key add -
RUN add-apt-repository "deb https://debian.neo4j.com stable 4.4"
RUN apt-get install -y neo4j

# grabs jar file needed to install apoc
RUN wget https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/4.4.0.30/apoc-4.4.0.30-all.jar -O /var/lib/neo4j/plugins/apoc-4.4.0.30-all.jar

# set custom configuration to enable apoc
RUN echo "dbms.security.procedures.unrestricted=apoc.*" >> /etc/neo4j/neo4j.conf
RUN echo "apoc.export.file.enabled=true" >> /etc/neo4j/neo4j.conf

# for coocurrence
COPY edges.tsv.gz /sw/edges.tsv.gz
COPY bio_entity_nodes.tsv.gz /sw/bio_entity_nodes.tsv.gz
COPY research_project_nodes.tsv.gz /sw/research_project_nodes.tsv.gz

# ingest graph content into neo4j
RUN sed -i 's/#dbms.default_listen_address/dbms.default_listen_address/' /etc/neo4j/neo4j.conf
RUN sed -i 's/#dbms.security.auth_enabled/dbms.security.auth_enabled/' /etc/neo4j/neo4j.conf
RUN neo4j-admin import --delimiter='TAB' --skip-duplicate-nodes=true --skip-bad-relationships=true \
    --relationships /sw/edges.tsv.gz \
    --nodes /sw/bio_entity_nodes.tsv.gz \
    --nodes /sw/research_project_nodes.tsv.gz

ENV DOCKERIZED="TRUE"
ENV NEO4J_URL="bolt://localhost:7687"

COPY startup.sh /sw/startup.sh

ENTRYPOINT ["/bin/bash", "/sw/startup.sh"]
