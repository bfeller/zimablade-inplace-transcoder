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
    intel-media-va-driver \
    vainfo \
    curl \
    su-exec \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY entrypoint.sh ./entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 transcoder

# Create data directories with proper ownership
RUN mkdir -p /data/{database,logs,temp/{working,completed,failed}} && \
    chown -R transcoder:transcoder /data && \
    chmod -R 755 /data

# Make entrypoint script executable
RUN chmod +x ./entrypoint.sh

# Note: We don't switch to transcoder user here because the entrypoint
# needs to run as root to fix volume permissions, then switch to transcoder

# Expose any ports if needed (none for this application)
# EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]

# Default command
CMD ["python3", "src/main.py"]
