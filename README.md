# Zimablade In-Place Transcoder

A custom transcoding solution specifically designed for the zimablade homelab server, optimized for Intel Quick Sync hardware acceleration.

## Requirements

- **Automatic Detection**: Scan all library files to detect files that need transcoding
- **Working Directory**: Move files to a working directory during processing
- **Smart Replacement**: Replace original files with optimized versions using API updates
- **Resolution Target**: Convert all files to 1080p
- **Hardware Acceleration**: Use Intel Quick Sync available on zimablade
- **Filename Optimization**: Use descriptive filenames and update Sonarr/Radarr via API
- **Sonarr/Radarr Integration**: Update file paths in database after successful transcoding using API

## Project Plan

### Phase 1: Core Architecture
1. **File Scanner Module**
   - Scan `/mnt/MainStorage/movies` and `/mnt/MainStorage/tv`
   - Detect files that need transcoding (resolution > 1080p, unsupported codecs)
   - Maintain database of processed files to avoid reprocessing
   - Support file age filtering (only process files older than X hours)

2. **Transcoding Engine**
   - Use `ffmpeg` with Intel Quick Sync (`-hwaccel qsv`)
   - Target: 1080p H.264 video with AAC audio
   - Preserve subtitle tracks
   - Maintain original container format (mkv, mp4)

3. **File Management System**
   - Move source file to `/mnt/SSD/transcoding/working/`
   - Process with optimized filename (e.g., `Show.S01E01.1080p.mkv`)
   - Replace original file with transcoded version
   - Update Sonarr/Radarr database with new filename via API
   - Handle failures gracefully (restore original)

4. **Sonarr/Radarr Integration**
   - Update file paths in database using API after transcoding
   - Trigger library refresh to sync changes
   - Update file metadata (size, duration) in Sonarr/Radarr
   - Prevent false "missing file" alerts
   - Maintain database integrity

### Phase 2: Implementation Details

#### File Detection Logic
```bash
# Files that need transcoding:
- Resolution > 1080p (4K, 1440p, etc.)
- Unsupported codecs (AV1, older formats)
- Files not already processed (check database)

# Files to skip:
- Already 1080p or lower
- Recently downloaded (< 24 hours old)
- Already processed (database check)
```

#### Transcoding Parameters
```bash
# Convert everything to MP4 for universal compatibility
ffmpeg -hwaccel qsv -i input.mkv \
  -vf scale_qsv=1920:1080 \
  -c:v h264_qsv \
  -preset medium \
  -crf 23 \
  -c:a aac \
  -b:a 128k \
  -c:s mov_text \
  -map 0 \
  Show.S01E01.1080p.mp4

# Convert MP4 to MP4 (re-encode for quality)
ffmpeg -hwaccel qsv -i input.mp4 \
  -vf scale_qsv=1920:1080 \
  -c:v h264_qsv \
  -preset medium \
  -crf 23 \
  -c:a aac \
  -b:a 128k \
  -c:s mov_text \
  -map 0 \
  Movie.2024.1080p.mp4
```

**Key Benefits:**
- **Universal Compatibility**: MP4 works on all devices and players
- **Better Streaming**: Optimized for web streaming and mobile devices
- **Smaller File Size**: More efficient container format
- **Simplified Commands**: No need to match input/output filenames
- **Descriptive Names**: Clear quality indicators (`1080p`)
- **API Updates**: Sonarr/Radarr get updated with new filenames

#### Sonarr/Radarr API Integration
```bash
# After transcoding completes, update file paths:

# For Sonarr (TV Shows):
curl -X PUT "${SONARR_URL}/api/v3/episodefile/${episodeFileId}" \
  -H "X-Api-Key: ${SONARR_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"relativePath": "new/path/to/file.mkv"}'

# For Radarr (Movies):
curl -X PUT "${RADARR_URL}/api/v3/moviefile/${movieFileId}" \
  -H "X-Api-Key: ${RADARR_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"relativePath": "new/path/to/file.mkv"}'

# Then trigger rescan:
curl -X POST "${SONARR_URL}/api/v3/command" \
  -H "X-Api-Key: ${SONARR_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"name": "RescanSeries", "seriesId": 123}'
```

#### Directory Structure
```
/mnt/MainStorage/movies/          # Source files
/mnt/MainStorage/tv/              # Source files
/mnt/SSD/transcoding/
├── working/                      # Active transcoding
├── completed/                    # Successfully processed
├── failed/                       # Failed transcodes
└── database/                     # Processing history
```

### Phase 3: Docker Implementation

#### Container Features
- **Base Image**: Ubuntu with Intel Quick Sync support
- **Hardware Access**: `/dev/dri` device passthrough
- **Scheduling**: Run during off-peak hours (2 AM - 10 AM)
- **Monitoring**: Log all operations and provide statistics
- **Safety**: Atomic file replacement to prevent data loss

#### Environment Variables
```yaml
# Paths
MOVIES_PATH: /data/movies
TV_PATH: /data/tv
WORKING_PATH: /transcoding/working
COMPLETED_PATH: /transcoding/completed
FAILED_PATH: /transcoding/failed

# Processing
MIN_FILE_AGE_HOURS: 24
TARGET_RESOLUTION: 1080p
CRF_QUALITY: 23

# Sonarr/Radarr Integration
SONARR_URL: http://sonarr:7878
SONARR_API_KEY: your_sonarr_api_key
RADARR_URL: http://radarr:7878
RADARR_API_KEY: your_radarr_api_key

# Scheduling
START_TIME: "02:00"
END_TIME: "10:00"
```

### Phase 4: Safety & Monitoring

#### Safety Features
- **Atomic Operations**: Use temporary files and atomic moves
- **Backup Strategy**: Keep original files until transcoding verified
- **Rollback Capability**: Restore original files on failure
- **Database Integrity**: Track all operations for audit trail

#### Monitoring & Logging
- **Progress Tracking**: Real-time transcoding progress
- **Statistics**: Files processed, time saved, space saved
- **Error Handling**: Detailed error logs and recovery procedures
- **Health Checks**: Verify Intel Quick Sync availability

## Technical Specifications

### Hardware Requirements
- **CPU**: Intel processor with Quick Sync support
- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: 
  - Source: `/mnt/MainStorage` (large capacity)
  - Working: `/mnt/SSD` (fast SSD for transcoding)

### Software Stack
- **Container Runtime**: Docker with device passthrough
- **Transcoding**: FFmpeg with Intel Quick Sync
- **Database**: SQLite for processing history
- **Scheduling**: Cron-based or continuous monitoring
- **Logging**: Structured logging with rotation

## Deployment

### Docker Compose Configuration
```yaml
version: '3.8'
services:
  zimablade-transcoder:
    build: .
    environment:
      - MOVIES_PATH=/data/movies
      - TV_PATH=/data/tv
      - WORKING_PATH=/transcoding/working
      - MIN_FILE_AGE_HOURS=24
      - TARGET_RESOLUTION=1080p
      - SONARR_URL=http://sonarr:7878
      - SONARR_API_KEY=your_sonarr_api_key
      - RADARR_URL=http://radarr:7878
      - RADARR_API_KEY=your_radarr_api_key
    volumes:
      - /mnt/MainStorage/movies:/data/movies
      - /mnt/MainStorage/tv:/data/tv
      - /mnt/SSD/transcoding:/transcoding
    devices:
      - /dev/dri:/dev/dri
    restart: unless-stopped
    networks:
      - default  # Same network as Sonarr/Radarr
```

## Success Criteria

- ✅ Automatically detect and process files needing transcoding
- ✅ Use Intel Quick Sync for hardware acceleration
- ✅ Maintain original filenames and extensions
- ✅ Process files in-place without data loss
- ✅ Provide comprehensive logging and monitoring
- ✅ Handle failures gracefully with rollback capability
- ✅ Run efficiently during off-peak hours

## Next Steps

1. Create basic file scanner
2. Implement Intel Quick Sync transcoding
3. Build file management system
4. Add safety and monitoring features
5. Create Docker deployment
6. Test with sample files
7. Deploy to zimablade server
