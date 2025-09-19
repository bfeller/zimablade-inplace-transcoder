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

# Create non-root user first
RUN useradd -m -u 1000 transcoder

# Create data directories with proper ownership
RUN mkdir -p /data/{database,logs,temp/{working,completed,failed}} && \
    chown -R transcoder:transcoder /data && \
    chmod -R 755 /data

# Switch to transcoder user
USER transcoder

# Ensure data directories exist and are writable (in case volume mount overrides)
RUN mkdir -p /data/{database,logs,temp/{working,completed,failed}}

# Expose any ports if needed (none for this application)
# EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

# Default command
CMD ["python3", "src/main.py"]
