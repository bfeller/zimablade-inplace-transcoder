# Use Ubuntu 24.04 LTS with native FFmpeg 6.x
FROM ubuntu:24.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Force rebuild - increment this number to invalidate cache
ARG BUILD_VERSION=0.6.3-debug
ENV BUILD_VERSION=${BUILD_VERSION}
ENV FORCE_REBUILD=${BUILD_VERSION}

# Install Python and basic tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-requests \
    python3-yaml \
    curl \
    sudo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install FFmpeg from Ubuntu repositories (stable and reliable)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Intel media driver and VAAPI utilities (Ubuntu 24.04)
RUN apt-get update && apt-get install -y --no-install-recommends \
    intel-media-va-driver-non-free \
    vainfo \
    libmfx1 \
    libmfx-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* || echo "Intel driver not available"

# Create application directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY entrypoint.sh ./entrypoint.sh

# Verify Python packages are working
RUN python3 -c "import requests, yaml; print('Python dependencies verified successfully')"

# Verify FFmpeg version and QSV support (like Jellyfin)
RUN ffmpeg -version | head -1
RUN ffmpeg -encoders | grep -i qsv || echo "No QSV encoders found"
RUN ffmpeg -hwaccels | grep -i qsv || echo "No QSV hardware acceleration found"
RUN vainfo || echo "VAAPI not available"

# AGGRESSIVE CACHE BUSTING - Force complete rebuild
RUN echo "BUILD_VERSION: ${BUILD_VERSION}" > /tmp/build_info.txt
RUN echo "FORCE_REBUILD: ${FORCE_REBUILD}" >> /tmp/build_info.txt
RUN echo "CACHE_BUSTING_TIMESTAMP: $(date)" >> /tmp/build_info.txt
RUN cat /tmp/build_info.txt


# Clear Python bytecode cache to prevent caching issues
RUN find ./src -name "*.pyc" -delete && find ./src -name "__pycache__" -type d -exec rm -rf {} + || true

# Additional cache clearing before runtime
RUN python3 -Bc "import compileall; compileall.compile_dir('./src', force=True)" || true

# Nuclear option: Remove all Python cache and force recompilation
RUN find ./src -name "*.pyc" -delete && find ./src -name "__pycache__" -type d -exec rm -rf {} + || true
RUN python3 -c "import py_compile; import os; [py_compile.compile(os.path.join(root, file), doraise=True) for root, dirs, files in os.walk('./src') for file in files if file.endswith('.py')]" || true

# Create non-root user (only if it doesn't exist)
RUN useradd -m -u 1000 transcoder || echo "User transcoder already exists"

# Create data directories (ownership handled by entrypoint)
RUN mkdir -p /data/{database,logs,temp/{working,completed,failed}} && \
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
