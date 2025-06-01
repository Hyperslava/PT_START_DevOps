FROM postgres:17

COPY init.sql /docker-entrypoint-initdb.d/
COPY pg_hba.conf /docker-entrypoint-initdb.d/

RUN apt-get update && apt-get install -y ssl-cert && \
    make-ssl-cert generate-default-snakeoil --force-overwrite

EXPOSE 5442

