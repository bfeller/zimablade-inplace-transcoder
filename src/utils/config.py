"""
Configuration management for the transcoder application.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Optional
from datetime import time


class Config:
    """Configuration manager for the transcoder application."""
    
    def __init__(self, config_dir: str = None):
        """Initialize configuration."""
        self.config_dir = config_dir or os.getenv('CONFIG_DIR', 'config')
        self.logger = logging.getLogger(__name__)
        
        # Load configuration files
        self._load_config()
    
    def _load_config(self):
        """Load configuration from files and environment variables."""
        # Default values
        self.movies_path = os.getenv('MOVIES_PATH', '/data/movies')
        self.tv_path = os.getenv('TV_PATH', '/data/tv')
        self.working_path = os.getenv('WORKING_PATH', '/data/temp/working')
        self.completed_path = os.getenv('COMPLETED_PATH', '/data/temp/completed')
        self.failed_path = os.getenv('FAILED_PATH', '/data/temp/failed')
        self.database_path = os.getenv('DATABASE_PATH', '/data/database/transcoding.db')
        
        # Processing settings
        self.min_file_age_hours = int(os.getenv('MIN_FILE_AGE_HOURS', '24'))
        self.min_bitrate_kbps = int(os.getenv('MIN_BITRATE_KBPS', '500'))
        self.sleep_interval = int(os.getenv('SLEEP_INTERVAL', '300'))  # 5 minutes
        
        # Time window settings
        start_time_str = os.getenv('START_TIME', '02:00')
        end_time_str = os.getenv('END_TIME', '10:00')
        self.start_time = self._parse_time(start_time_str)
        self.end_time = self._parse_time(end_time_str)
        
        # Transcoding settings
        self.crf_quality = int(os.getenv('CRF_QUALITY', '23'))
        self.audio_bitrate = int(os.getenv('AUDIO_BITRATE', '128'))
        self.target_resolution = os.getenv('TARGET_RESOLUTION', '1080p')
        self.preset = os.getenv('FFMPEG_PRESET', 'medium')
        
        # Hardware acceleration
        self.use_hardware_acceleration = os.getenv('USE_HWACCEL', 'true').lower() == 'true'
        self.hardware_accel = os.getenv('HARDWARE_ACCEL', 'qsv')
        
        # File management
        self.create_backups = os.getenv('CREATE_BACKUPS', 'false').lower() == 'true'
        
        # Sonarr/Radarr settings
        self.sonarr_enabled = os.getenv('SONARR_ENABLED', 'true').lower() == 'true'
        self.sonarr_url = os.getenv('SONARR_URL', 'http://sonarr:7878')
        self.sonarr_api_key = os.getenv('SONARR_API_KEY', '')
        
        self.radarr_enabled = os.getenv('RADARR_ENABLED', 'true').lower() == 'true'
        self.radarr_url = os.getenv('RADARR_URL', 'http://radarr:7878')
        self.radarr_api_key = os.getenv('RADARR_API_KEY', '')
        
        # Logging settings
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', '/data/logs/transcoder.log')
        self.log_max_size = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB
        self.log_backup_count = int(os.getenv('LOG_BACKUP_COUNT', '5'))
        
        # Debug mode
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        
        # Load additional config from YAML files
        self._load_yaml_configs()
        
        self.logger.debug("Configuration loaded successfully")
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string to time object."""
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        except ValueError:
            self.logger.warning("Invalid time format: %s, using default", time_str)
            return time(2, 0)  # Default to 2:00 AM
    
    def _load_yaml_configs(self):
        """Load additional configuration from YAML files."""
        config_path = Path(self.config_dir)
        
        if not config_path.exists():
            self.logger.warning("Config directory does not exist: %s", config_path)
            return
        
        # Load transcoding config
        transcoding_config = config_path / 'transcoding.yaml'
        if transcoding_config.exists():
            try:
                with open(transcoding_config, 'r') as f:
                    transcoding_data = yaml.safe_load(f)
                    self._apply_transcoding_config(transcoding_data)
            except Exception as e:
                self.logger.warning("Failed to load transcoding config: %s", e)
        
        # Load logging config
        logging_config = config_path / 'logging.yaml'
        if logging_config.exists():
            try:
                with open(logging_config, 'r') as f:
                    logging_data = yaml.safe_load(f)
                    self._apply_logging_config(logging_data)
            except Exception as e:
                self.logger.warning("Failed to load logging config: %s", e)
    
    def _apply_transcoding_config(self, config: dict):
        """Apply transcoding configuration from YAML."""
        if 'quality' in config:
            self.crf_quality = config['quality'].get('crf', self.crf_quality)
            self.audio_bitrate = config['quality'].get('audio_bitrate', self.audio_bitrate)
        
        if 'hardware' in config:
            self.use_hardware_acceleration = config['hardware'].get('enabled', self.use_hardware_acceleration)
            self.hardware_accel = config['hardware'].get('type', self.hardware_accel)
        
        if 'target' in config:
            self.target_resolution = config['target'].get('resolution', self.target_resolution)
            self.preset = config['target'].get('preset', self.preset)
    
    def _apply_logging_config(self, config: dict):
        """Apply logging configuration from YAML."""
        if 'level' in config:
            self.log_level = config['level']
        
        if 'file' in config:
            self.log_file = config['file']
        
        if 'rotation' in config:
            self.log_max_size = config['rotation'].get('max_size', self.log_max_size)
            self.log_backup_count = config['rotation'].get('backup_count', self.log_backup_count)
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        errors = []
        
        # Check required paths
        if not self.movies_path and not self.tv_path:
            errors.append("At least one of MOVIES_PATH or TV_PATH must be set")
        
        # Check API keys if services are enabled
        if self.sonarr_enabled and not self.sonarr_api_key:
            errors.append("SONARR_API_KEY is required when Sonarr is enabled")
        
        if self.radarr_enabled and not self.radarr_api_key:
            errors.append("RADARR_API_KEY is required when Radarr is enabled")
        
        # Check time window
        if self.start_time == self.end_time:
            errors.append("START_TIME and END_TIME cannot be the same")
        
        # Check transcoding settings
        if not (0 <= self.crf_quality <= 51):
            errors.append("CRF_QUALITY must be between 0 and 51")
        
        if self.audio_bitrate < 64 or self.audio_bitrate > 320:
            errors.append("AUDIO_BITRATE must be between 64 and 320")
        
        if errors:
            for error in errors:
                self.logger.error("Configuration error: %s", error)
            return False
        
        self.logger.info("Configuration validation passed")
        return True
    
    def get_ffmpeg_args(self) -> list:
        """Get FFmpeg arguments based on configuration."""
        args = []
        
        if self.use_hardware_acceleration:
            args.extend(['-hwaccel', self.hardware_accel])
        
        args.extend([
            '-vf', f'scale_{self.hardware_accel}=1920:1080',
            '-c:v', f'h264_{self.hardware_accel}',
            '-preset', self.preset,
            '-crf', str(self.crf_quality),
            '-c:a', 'aac',
            '-b:a', f'{self.audio_bitrate}k',
            '-c:s', 'mov_text',
            '-map', '0',
            '-y'
        ])
        
        return args
