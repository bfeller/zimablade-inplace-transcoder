#!/bin/bash

# Ensure data directories exist
mkdir -p /data/{database,logs,temp/{working,completed,failed}}

# Execute the main application directly
# We're already running as the correct user (1000:1000) with proper group access
exec "$@"
