"""
Data models for the transcoder application.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class FileInfo:
    """Information about a video file."""
    path: Path
    filename: str
    size_bytes: int
    duration_seconds: float
    width: int
    height: int
    codec: str
    bitrate: int
    is_tv_show: bool
    is_movie: bool
    
    @property
    def resolution(self) -> str:
        """Get resolution string (e.g., '1080p', '4K')."""
        if self.height >= 2160:
            return '4K'
        elif self.height >= 1440:
            return '1440p'
        elif self.height >= 1080:
            return '1080p'
        elif self.height >= 720:
            return '720p'
        else:
            return f'{self.height}p'
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB."""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def bitrate_kbps(self) -> int:
        """Get bitrate in kbps."""
        return self.bitrate // 1000
    
    @property
    def duration_minutes(self) -> float:
        """Get duration in minutes."""
        return self.duration_seconds / 60


@dataclass
class TranscodingJob:
    """Represents a transcoding job."""
    file_info: FileInfo
    input_path: str
    output_path: str
    status: str = 'pending'  # pending, processing, completed, failed
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    
    @property
    def processing_time(self) -> Optional[float]:
        """Get processing time in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def is_completed(self) -> bool:
        """Check if job is completed."""
        return self.status == 'completed'
    
    @property
    def is_failed(self) -> bool:
        """Check if job failed."""
        return self.status == 'failed'


@dataclass
class ProcessingStats:
    """Processing statistics for a time period."""
    date: str
    files_processed: int
    total_size_saved: int
    total_processing_time: int
    avg_processing_time: float
    success_rate: float
    
    @property
    def size_saved_mb(self) -> float:
        """Get size saved in MB."""
        return self.total_size_saved / (1024 * 1024)
    
    @property
    def size_saved_gb(self) -> float:
        """Get size saved in GB."""
        return self.total_size_saved / (1024 * 1024 * 1024)
    
    @property
    def processing_time_hours(self) -> float:
        """Get processing time in hours."""
        return self.total_processing_time / 3600


@dataclass
class APIConfig:
    """Configuration for API clients."""
    base_url: str
    api_key: str
    timeout: int = 30
    
    @property
    def headers(self) -> dict:
        """Get headers for API requests."""
        return {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }


@dataclass
class TranscodingConfig:
    """Transcoding configuration."""
    crf_quality: int = 23
    audio_bitrate: int = 128
    target_resolution: str = '1080p'
    target_width: int = 1920
    target_height: int = 1080
    preset: str = 'medium'
    use_hardware_acceleration: bool = True
    hardware_accel: str = 'qsv'
