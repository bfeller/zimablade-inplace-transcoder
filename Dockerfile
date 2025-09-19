# Use Ubuntu 22.04 LTS with newer FFmpeg from PPA (more stable)
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Force rebuild - increment this number to invalidate cache
ARG BUILD_VERSION=0.4.3-debug
ENV BUILD_VERSION=${BUILD_VERSION}
ENV FORCE_REBUILD=${BUILD_VERSION}

# Install basic system dependencies first
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    gosu \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "Basic dependencies installed successfully"

# Install additional packages separately
RUN apt-get update && apt-get install -y \
    python3-venv \
    python3-dev \
    software-properties-common \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "Additional dependencies installed successfully"

# Install FFmpeg with QSV support from PPA (Ubuntu 22.04 compatible)
RUN add-apt-repository ppa:savoury1/ffmpeg4 -y && \
    apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    echo "FFmpeg with QSV support installed successfully"

# Install Intel media driver and VAAPI utilities (Ubuntu 22.04 compatible)
RUN apt-get update && apt-get install -y \
    intel-media-va-driver \
    vainfo \
    libmfx1 \
    libmfx-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "Intel media driver and VAAPI utilities installed successfully" || \
    echo "Intel media driver not available, skipping"

# Create application directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir -r requirements.txt
RUN python3 -c "import requests, yaml; print('Dependencies installed successfully')"

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY entrypoint.sh ./entrypoint.sh

# AGGRESSIVE CACHE BUSTING - Force complete rebuild
RUN echo "BUILD_VERSION: ${BUILD_VERSION}" > /tmp/build_info.txt
RUN echo "FORCE_REBUILD: ${FORCE_REBUILD}" >> /tmp/build_info.txt
RUN echo "CACHE_BUSTING_TIMESTAMP: $(date)" >> /tmp/build_info.txt
RUN cat /tmp/build_info.txt

# Verify FFmpeg version and Intel Quick Sync support
RUN ffmpeg -version | head -1
RUN ffmpeg -encoders | grep -i qsv || echo "No QSV encoders found"
RUN ffmpeg -hwaccels | grep -i qsv || echo "No QSV hardware acceleration found"
RUN vainfo || echo "VAAPI not available"

# Clear Python bytecode cache to prevent caching issues
RUN find ./src -name "*.pyc" -delete && find ./src -name "__pycache__" -type d -exec rm -rf {} + || true

# Additional cache clearing before runtime
RUN python3 -Bc "import compileall; compileall.compile_dir('./src', force=True)" || true

# Nuclear option: Remove all Python cache and force recompilation
RUN find ./src -name "*.pyc" -delete && find ./src -name "__pycache__" -type d -exec rm -rf {} + || true
RUN python3 -c "import py_compile; import os; [py_compile.compile(os.path.join(root, file), doraise=True) for root, dirs, files in os.walk('./src') for file in files if file.endswith('.py')]" || true

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
