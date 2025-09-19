#!/bin/bash

# Ensure data directories exist and have proper permissions
mkdir -p /data/{database,logs,temp/{working,completed,failed}}

# Set proper permissions for the transcoder user
chmod -R 755 /data

# Execute the main application
exec "$@"
