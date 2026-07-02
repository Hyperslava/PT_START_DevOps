FROM postgres:17

COPY init.sql /docker-entrypoint-initdb.d/
COPY configure-replication.sh /docker-entrypoint-initdb.d/
RUN chmod 0755 /docker-entrypoint-initdb.d/configure-replication.sh

RUN apt-get update && apt-get install -y ssl-cert && \
    make-ssl-cert generate-default-snakeoil --force-overwrite

RUN mkdir -p /var/log/postgresql && chown postgres:postgres /var/log/postgresql

EXPOSE 5442

