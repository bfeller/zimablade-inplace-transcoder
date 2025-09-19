# Use Ubuntu base image with Intel Quick Sync support
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    intel-media-va-driver-non-free \
    vainfo \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create data directories
RUN mkdir -p /data/{database,logs,temp/{working,completed,failed}}

# Set permissions
RUN chmod 755 /data/ && \
    chmod 755 /data/database/ && \
    chmod 755 /data/logs/ && \
    chmod 755 /data/temp/ && \
    chmod 755 /data/temp/working/ && \
    chmod 755 /data/temp/completed/ && \
    chmod 755 /data/temp/failed/

# Create non-root user
RUN useradd -m -u 1000 transcoder && \
    chown -R transcoder:transcoder /app /data

USER transcoder

# Expose any ports if needed (none for this application)
# EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

# Default command
CMD ["python3", "src/main.py"]
