"""
File scanner module for detecting files that need transcoding.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

from models.file_info import FileInfo
from utils.helpers import get_video_info


class FileScanner:
    """Scans directories for files that need transcoding."""
    
    def __init__(self, config, database):
        """Initialize the file scanner."""
        self.config = config
        self.db = database
        self.logger = logging.getLogger(__name__)
        
        # Supported video extensions
        self.video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.m4v'}
        
        # Quality patterns to detect high-resolution content
        self.quality_patterns = {
            '2160p', '4K', 'UHD', '2160', '4k', 'uhd',
            '1440p', '2K', '1440', '2k',
            '1080p', '1080',  # Only if not already optimized
        }
    
    def scan_for_files(self) -> List[FileInfo]:
        """Scan configured directories for files that need transcoding."""
        files_to_process = []
        
        # Scan movies directory
        if self.config.movies_path and os.path.exists(self.config.movies_path):
            movie_files = self._scan_directory(self.config.movies_path, is_tv=False)
            files_to_process.extend(movie_files)
        
        # Scan TV shows directory
        if self.config.tv_path and os.path.exists(self.config.tv_path):
            tv_files = self._scan_directory(self.config.tv_path, is_tv=True)
            files_to_process.extend(tv_files)
        
        self.logger.info("Found %d files total for processing", len(files_to_process))
        return files_to_process
    
    def _scan_directory(self, directory: str, is_tv: bool) -> List[FileInfo]:
        """Scan a single directory for files."""
        files = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            self.logger.warning("Directory does not exist: %s", directory)
            return files
        
        # Walk through directory recursively
        for file_path in directory_path.rglob('*'):
            if self._should_process_file(file_path):
                file_info = self._analyze_file(file_path, is_tv)
                if file_info and self._needs_transcoding(file_info):
                    files.append(file_info)
        
        self.logger.info("Found %d files in %s", len(files), directory)
        return files
    
    def _should_process_file(self, file_path: Path) -> bool:
        """Check if a file should be considered for processing."""
        # Check extension
        if file_path.suffix.lower() not in self.video_extensions:
            return False
        
        # Check if file exists and is readable
        if not file_path.exists() or not file_path.is_file():
            return False
        
        # Check file age (skip recently downloaded files)
        if self._is_file_too_recent(file_path):
            return False
        
        # Check if already processed
        if self.db.is_file_processed(file_path):
            return False
        
        return True
    
    def _is_file_too_recent(self, file_path: Path) -> bool:
        """Check if file is too recent to process."""
        try:
            file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
            min_age = timedelta(hours=self.config.min_file_age_hours)
            return file_age < min_age
        except OSError:
            return True  # Skip if we can't get file stats
    
    def _analyze_file(self, file_path: Path, is_tv: bool) -> Optional[FileInfo]:
        """Analyze a file and return FileInfo if it's a valid video file."""
        try:
            # Get video information using ffprobe
            video_info = get_video_info(str(file_path))
            
            if not video_info:
                return None
            
            # Create FileInfo object
            file_info = FileInfo(
                path=file_path,
                filename=file_path.name,
                size_bytes=file_path.stat().st_size,
                duration_seconds=video_info.get('duration', 0),
                width=video_info.get('width', 0),
                height=video_info.get('height', 0),
                codec=video_info.get('codec', 'unknown'),
                bitrate=video_info.get('bitrate', 0),
                is_tv_show=is_tv,
                is_movie=not is_tv
            )
            
            return file_info
            
        except Exception as e:
            self.logger.warning("Failed to analyze file %s: %s", file_path, e)
            return None
    
    def _needs_transcoding(self, file_info: FileInfo) -> bool:
        """Determine if a file needs transcoding."""
        # Check resolution - only process files > 1080p
        if file_info.height <= 1080:
            self.logger.debug("Skipping %s: resolution %dp <= 1080p", 
                            file_info.filename, file_info.height)
            return False
        
        # Check if filename indicates high quality
        filename_lower = file_info.filename.lower()
        has_quality_indicator = any(pattern in filename_lower 
                                  for pattern in self.quality_patterns)
        
        if not has_quality_indicator:
            self.logger.debug("Skipping %s: no quality indicator in filename", 
                            file_info.filename)
            return False
        
        # Check codec - skip if already H.264
        if file_info.codec.lower() in ['h264', 'avc']:
            self.logger.debug("Skipping %s: already H.264", file_info.filename)
            return False
        
        # Check bitrate - skip very low bitrate files
        if file_info.bitrate < self.config.min_bitrate_kbps * 1000:
            self.logger.debug("Skipping %s: bitrate too low (%d kbps)", 
                            file_info.filename, file_info.bitrate // 1000)
            return False
        
        self.logger.info("File needs transcoding: %s (%dp, %s, %d kbps)", 
                        file_info.filename, file_info.height, 
                        file_info.codec, file_info.bitrate // 1000)
        return True
