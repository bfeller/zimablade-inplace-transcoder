"""
File management module for handling file operations during transcoding.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional


class FileManager:
    """Manages file operations during the transcoding process."""
    
    def __init__(self, config):
        """Initialize the file manager."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Ensure working directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.config.working_path,
            self.config.completed_path,
            self.config.failed_path
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            self.logger.debug("Ensured directory exists: %s", directory)
    
    def move_to_working(self, file_path: str) -> str:
        """Move file to working directory for transcoding."""
        try:
            source_path = Path(file_path)
            working_filename = f"working_{source_path.name}"
            working_path = Path(self.config.working_path) / working_filename
            
            self.logger.info("Moving to working directory: %s -> %s", 
                           file_path, working_path)
            
            # Move file atomically
            shutil.move(str(source_path), str(working_path))
            
            return str(working_path)
            
        except Exception as e:
            self.logger.error("Failed to move file to working directory: %s", e)
            raise
    
    def get_output_path(self, filename: str) -> str:
        """Get the full path for output file."""
        return str(Path(self.config.working_path) / filename)
    
    def replace_original(self, original_path: str, transcoded_path: str) -> bool:
        """Replace original file with transcoded version."""
        try:
            original_file = Path(original_path)
            transcoded_file = Path(transcoded_path)
            
            self.logger.info("Replacing original file: %s", original_path)
            
            # Create backup of original (optional)
            if self.config.create_backups:
                backup_path = original_file.with_suffix(original_file.suffix + '.backup')
                shutil.copy2(str(original_file), str(backup_path))
                self.logger.debug("Created backup: %s", backup_path)
            
            # Atomic replacement
            temp_path = original_file.with_suffix(original_file.suffix + '.tmp')
            shutil.move(str(transcoded_file), str(temp_path))
            shutil.move(str(temp_path), str(original_file))
            
            self.logger.info("Successfully replaced original file")
            return True
            
        except Exception as e:
            self.logger.error("Failed to replace original file: %s", e)
            return False
    
    def restore_original(self, original_path: str, working_path: str) -> bool:
        """Restore original file from working directory."""
        try:
            original_file = Path(original_path)
            working_file = Path(working_path)
            
            self.logger.info("Restoring original file: %s", original_path)
            
            # Move working file back to original location
            shutil.move(str(working_file), str(original_file))
            
            self.logger.info("Successfully restored original file")
            return True
            
        except Exception as e:
            self.logger.error("Failed to restore original file: %s", e)
            return False
    
    def move_to_completed(self, file_path: str) -> bool:
        """Move file to completed directory."""
        try:
            source_path = Path(file_path)
            completed_path = Path(self.config.completed_path) / source_path.name
            
            self.logger.info("Moving to completed directory: %s", file_path)
            shutil.move(str(source_path), str(completed_path))
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to move file to completed directory: %s", e)
            return False
    
    def move_to_failed(self, file_path: str) -> bool:
        """Move file to failed directory."""
        try:
            source_path = Path(file_path)
            failed_path = Path(self.config.failed_path) / source_path.name
            
            self.logger.info("Moving to failed directory: %s", file_path)
            shutil.move(str(source_path), str(failed_path))
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to move file to failed directory: %s", e)
            return False
    
    def cleanup_working_directory(self) -> int:
        """Clean up old files from working directory."""
        try:
            working_dir = Path(self.config.working_path)
            cleaned_count = 0
            
            # Remove files older than 24 hours
            for file_path in working_dir.iterdir():
                if file_path.is_file():
                    file_age = file_path.stat().st_mtime
                    current_time = os.path.getmtime(str(working_dir))
                    
                    # If file is older than 24 hours, remove it
                    if current_time - file_age > 86400:  # 24 hours in seconds
                        file_path.unlink()
                        cleaned_count += 1
                        self.logger.debug("Cleaned up old file: %s", file_path)
            
            if cleaned_count > 0:
                self.logger.info("Cleaned up %d old files from working directory", cleaned_count)
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error("Failed to cleanup working directory: %s", e)
            return 0
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        try:
            return Path(file_path).stat().st_size
        except OSError:
            return 0
    
    def get_available_space(self, path: str) -> int:
        """Get available disk space in bytes."""
        try:
            stat = shutil.disk_usage(path)
            return stat.free
        except OSError:
            return 0
    
    def has_enough_space(self, file_path: str, required_space: int) -> bool:
        """Check if there's enough space for transcoding."""
        available_space = self.get_available_space(file_path)
        
        # Require 3x the file size for transcoding
        required_space = required_space * 3
        
        return available_space >= required_space
