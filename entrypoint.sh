#!/bin/bash

# Get PUID and PGID from environment variables
PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Ensure data directories exist
mkdir -p /data/{database,logs,temp/{working,completed,failed}}

# Fix ownership and permissions for the mounted volumes
# This needs to run as root to change ownership of mounted volumes
chown -R ${PUID}:${PGID} /data
chmod -R 755 /data

# Switch to the non-root user and execute the main application
exec su-exec ${PUID}:${PGID} "$@"
