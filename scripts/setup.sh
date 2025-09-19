#!/bin/bash

# Zimablade Transcoder Setup Script

set -e

echo "🚀 Setting up Zimablade Transcoder..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/{database,logs,temp/{working,completed,failed}}
mkdir -p /DATA/AppData/zimablade-transcoder

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 data/
chmod 755 data/database/
chmod 755 data/logs/
chmod 755 data/temp/
chmod 755 data/temp/working/
chmod 755 data/temp/completed/
chmod 755 data/temp/failed/

# Copy environment template
if [ ! -f .env ]; then
    echo "📝 Creating environment file..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your API keys and settings"
else
    echo "✅ Environment file already exists"
fi

# Check Intel Quick Sync support
echo "🔍 Checking Intel Quick Sync support..."
if command -v vainfo &> /dev/null; then
    if vainfo 2>/dev/null | grep -q "iHD"; then
        echo "✅ Intel Quick Sync is available"
    else
        echo "⚠️  Intel Quick Sync may not be available"
    fi
else
    echo "⚠️  vainfo not found, cannot check Intel Quick Sync"
fi

# Check FFmpeg installation
echo "🔍 Checking FFmpeg installation..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg is installed"
    ffmpeg -version | head -1
else
    echo "❌ FFmpeg is not installed"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Sonarr/Radarr API keys"
echo "2. Run: docker-compose up -d"
echo "3. Check logs: docker-compose logs -f"
echo ""
echo "Configuration files:"
echo "- config/transcoding.yaml - Transcoding settings"
echo "- config/logging.yaml - Logging settings"
echo "- .env - Environment variables"
echo ""
echo "For more information, see README.md"
