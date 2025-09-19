"""
Main application entry point for Zimablade Transcoder.
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from core.scanner import FileScanner
from core.transcoder import Transcoder
from core.file_manager import FileManager
from core.database import Database
from integrations.sonarr import SonarrClient
from integrations.radarr import RadarrClient
from utils.config import Config
from utils.logging import setup_logging

__version__ = "0.3.5-debug"


class ZimabladeTranscoder:
    """Main transcoder application class."""
    
    def __init__(self):
        """Initialize the transcoder application."""
        self.config = Config()
        self.logger = setup_logging()
        self.db = Database(self.config.database_path)
        self.scanner = FileScanner(self.config, self.db)
        self.transcoder = Transcoder(self.config)
        self.file_manager = FileManager(self.config)
        self.sonarr = SonarrClient(self.config) if self.config.sonarr_enabled else None
        self.radarr = RadarrClient(self.config) if self.config.radarr_enabled else None
        
        # Test connections to media servers
        self._test_media_server_connections()
    
    def _test_media_server_connections(self):
        """Test connections to Sonarr/Radarr and disable if not available."""
        if self.sonarr:
            if not self.sonarr.test_connection():
                self.logger.error("Sonarr connection failed - disabling transcoding")
                self.sonarr = None
            else:
                self.logger.info("Sonarr connection successful")
        
        if self.radarr:
            if not self.radarr.test_connection():
                self.logger.error("Radarr connection failed - disabling transcoding")
                self.radarr = None
            else:
                self.logger.info("Radarr connection successful")
        
        # Check if any media server is available
        if not self.sonarr and not self.radarr:
            self.logger.error("No media servers available - transcoding disabled")
            self.logger.error("Please check Sonarr/Radarr connections and API keys")
            raise RuntimeError("No media servers available - cannot proceed with transcoding")
        
    def run(self):
        """Main application loop."""
        self.logger.info("Starting Zimablade Transcoder v%s", __version__)
        
        try:
            # Initialize database
            self.db.initialize()
            
            # Clear database if requested
            if self.config.clear_database_on_start:
                self.logger.warning("CLEAR_DATABASE_ON_START is enabled - clearing all database data")
                self.db.clear_all_data()
                self.logger.warning("Database cleared - all files will be reanalyzed")
            
            # Log database stats for debugging
            if self.config.debug_mode:
                stats = self.db.get_database_stats()
                self.logger.info("Database stats: %s", stats)
            
            # Main processing loop
            while True:
                if self._should_process():
                    self._process_files()
                else:
                    self.logger.info("Outside processing window, sleeping...")
                
                # Sleep for configured interval
                time.sleep(self.config.sleep_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            self.logger.error("Fatal error: %s", e, exc_info=True)
            raise
        finally:
            self._cleanup()
    
    def _should_process(self) -> bool:
        """Check if we should process files based on time window."""
        # In debug mode, always process regardless of time
        if self.config.debug_mode:
            self.logger.info("DEBUG MODE: Ignoring time window restrictions")
            return True
        
        now = datetime.now().time()
        start_time = self.config.start_time
        end_time = self.config.end_time
        
        if start_time <= end_time:
            return start_time <= now <= end_time
        else:
            # Handle overnight processing (e.g., 22:00 to 06:00)
            return now >= start_time or now <= end_time
    
    def _process_files(self):
        """Main file processing logic."""
        self.logger.info("Starting file processing cycle")
        
        
        # Scan for files that need transcoding
        try:
            files_to_process = self.scanner.scan_for_files()
        except Exception as e:
            self.logger.error("Error during file scanning: %s", e, exc_info=True)
            files_to_process = []
        
        if not files_to_process:
            self.logger.info("No files found for processing")
            return
        
        self.logger.info("Found %d files to process", len(files_to_process))
        
        # Debug mode: process only the first file and exit
        if self.config.debug_mode:
            self.logger.info("DEBUG MODE: Processing only the first file and exiting")
            file_info = files_to_process[0]
            
            # Determine if it's a TV show or movie
            media_type = "TV Show" if file_info.is_tv_show else "Movie"
            self.logger.info("DEBUG MODE: Processing %s: %s", media_type, file_info.path)
            
            try:
                self._process_single_file(file_info)
                self.logger.info("DEBUG MODE: Successfully processed %s", media_type)
            except Exception as e:
                self.logger.error("DEBUG MODE: Failed to process %s: %s", file_info.path, e)
                self.file_manager.move_to_failed(file_info.path)
            
            self.logger.info("DEBUG MODE: Exiting after processing one file")
            return
        
        # Normal mode: process all files
        for file_info in files_to_process:
            try:
                self._process_single_file(file_info)
            except Exception as e:
                self.logger.error("Failed to process %s: %s", file_info.path, e)
                # Move to failed directory
                self.file_manager.move_to_failed(file_info.path)
    
    def _process_single_file(self, file_info):
        """Process a single file through the transcoding pipeline."""
        self.logger.info("Processing: %s", file_info.path)
        
        # Move file to working directory
        working_path = self.file_manager.move_to_working(file_info.path)
        
        try:
            # Generate output filename
            output_filename = self._generate_output_filename(file_info)
            output_path = self.file_manager.get_output_path(output_filename)
            
            # Transcode the file (pass original path for HDR detection)
            self.logger.info("About to call transcoder.transcode() with working_path=%s, output_path=%s, original_path=%s", 
                           working_path, output_path, file_info.path)
            success = self.transcoder.transcode(working_path, output_path, file_info.path)
            self.logger.info("Transcoder returned success=%s", success)
            
            if success:
                # Replace original file
                self.file_manager.replace_original(file_info.path, output_path)
                
                # Update Sonarr/Radarr
                self._update_media_servers(file_info, output_filename)
                
                # Update database
                self.db.mark_as_processed(file_info.path, output_filename, file_info.__dict__)
                
                self.logger.info("Successfully processed: %s", file_info.path)
            else:
                self.logger.error("Transcoding failed for %s", file_info.path)
                # Don't raise exception - let the transcoder handle retries internally
                # The transcoder will have already tried both Intel Quick Sync and software encoding
                return
                
        except Exception as e:
            self.logger.error("Failed to process %s: %s", file_info.path, e)
            # Restore original file
            self.file_manager.restore_original(file_info.path, working_path)
            raise
    
    def _generate_output_filename(self, file_info):
        """Generate output filename based on input file."""
        # Extract base name without extension
        base_name = file_info.path.stem
        
        # Remove quality indicators (2160p, 4K, etc.)
        quality_patterns = ['2160p', '4K', 'UHD', '1080p', '720p', '480p']
        for pattern in quality_patterns:
            base_name = base_name.replace(f'.{pattern}', '').replace(f'_{pattern}', '')
        
        # Add 1080p quality indicator
        return f"{base_name}.1080p.mp4"
    
    def _update_media_servers(self, file_info, output_filename):
        """Update Sonarr/Radarr with new filename."""
        try:
            if self.sonarr and file_info.is_tv_show:
                success = self.sonarr.update_file_path(file_info.path, output_filename)
                if not success:
                    raise Exception("Sonarr API update failed")
            elif self.radarr and file_info.is_movie:
                success = self.radarr.update_file_path(file_info.path, output_filename)
                if not success:
                    raise Exception("Radarr API update failed")
        except Exception as e:
            self.logger.error("Failed to update media server: %s", e)
            raise  # Re-raise to stop processing
    
    def _cleanup(self):
        """Cleanup resources on shutdown."""
        self.logger.info("Cleaning up resources...")
        
        # Clean up any files in working directory
        self._cleanup_working_files()
        
        # Close database connection
        if hasattr(self.db, 'close'):
            self.db.close()
    
    def _cleanup_working_files(self):
        """Clean up files in working directory on shutdown."""
        try:
            import shutil
            working_dir = Path(self.config.working_path)
            if working_dir.exists():
                for file_path in working_dir.iterdir():
                    if file_path.is_file():
                        self.logger.warning("Found unfinished transcoding file: %s", file_path.name)
                        # Move back to original location or failed directory
                        # This is a simplified cleanup - in production you'd want more sophisticated handling
                        failed_path = Path(self.config.failed_path) / file_path.name
                        try:
                            shutil.move(str(file_path), str(failed_path))
                            self.logger.info("Moved unfinished file to failed directory: %s", file_path.name)
                        except Exception as e:
                            self.logger.error("Failed to move unfinished file: %s", e)
        except Exception as e:
            self.logger.error("Error during cleanup: %s", e)


def main():
    """Main entry point."""
    transcoder = ZimabladeTranscoder()
    transcoder.run()


if __name__ == "__main__":
    main()
