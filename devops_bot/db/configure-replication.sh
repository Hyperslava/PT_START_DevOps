#!/bin/sh
set -eu

case "$POSTGRES_USER" in
  *[!a-zA-Z0-9_]*|'')
    echo "POSTGRES_USER contains unsupported characters" >&2
    exit 1
    ;;
esac

printf 'host replication %s samenet scram-sha-256\n' "$POSTGRES_USER" >> "$PGDATA/pg_hba.conf"
