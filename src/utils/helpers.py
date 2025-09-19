"""
Helper utility functions.
"""

import os
import json
import subprocess
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any


def get_video_info(file_path: str) -> Optional[Dict[str, Any]]:
    """Get video file information using ffprobe."""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return _parse_ffprobe_output(data)
        else:
            logging.getLogger(__name__).error("ffprobe failed: %s", result.stderr)
            return None
            
    except Exception as e:
        logging.getLogger(__name__).error("Error getting video info: %s", e)
        return None


def _parse_ffprobe_output(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse ffprobe JSON output to extract relevant information."""
    info = {
        'duration': 0,
        'width': 0,
        'height': 0,
        'codec': 'unknown',
        'bitrate': 0,
        'size': 0
    }
    
    try:
        # Get format information
        format_info = data.get('format', {})
        info['duration'] = float(format_info.get('duration', 0))
        info['bitrate'] = int(format_info.get('bit_rate', 0))
        info['size'] = int(format_info.get('size', 0))
        
        # Get video stream information
        streams = data.get('streams', [])
        video_stream = None
        
        for stream in streams:
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if video_stream:
            info['width'] = int(video_stream.get('width', 0))
            info['height'] = int(video_stream.get('height', 0))
            info['codec'] = video_stream.get('codec_name', 'unknown')
        
        return info
        
    except (ValueError, KeyError) as e:
        logging.getLogger(__name__).warning("Error parsing ffprobe output: %s", e)
        return info


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_bitrate(bitrate: int) -> str:
    """Format bitrate to human readable string."""
    if bitrate < 1000:
        return f"{bitrate} bps"
    elif bitrate < 1000000:
        return f"{bitrate / 1000:.1f} kbps"
    else:
        return f"{bitrate / 1000000:.1f} Mbps"


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    try:
        return Path(file_path).stat().st_size
    except OSError:
        return 0


def ensure_directory(path: str) -> bool:
    """Ensure directory exists, create if it doesn't."""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.getLogger(__name__).error("Failed to create directory %s: %s", path, e)
        return False


def is_video_file(file_path: str) -> bool:
    """Check if file is a video file based on extension."""
    video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.m4v', '.wmv', '.flv', '.webm'}
    return Path(file_path).suffix.lower() in video_extensions


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe use."""
    # Remove or replace problematic characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove multiple underscores
    while '__' in filename:
        filename = filename.replace('__', '_')
    
    # Remove leading/trailing underscores and dots
    filename = filename.strip('_.')
    
    return filename


def get_relative_path(file_path: str, base_path: str) -> str:
    """Get relative path from base path."""
    try:
        file_path_obj = Path(file_path)
        base_path_obj = Path(base_path)
        return str(file_path_obj.relative_to(base_path_obj))
    except ValueError:
        # If file_path is not relative to base_path, return the filename
        return Path(file_path).name


def estimate_transcoding_time(file_duration: float, resolution: str) -> float:
    """Estimate transcoding time based on file duration and resolution."""
    # Base multiplier for Intel Quick Sync (conservative estimate)
    base_multiplier = 0.1
    
    # Adjust based on resolution
    resolution_multipliers = {
        '4K': 0.15,
        '1440p': 0.12,
        '1080p': 0.1,
        '720p': 0.08
    }
    
    multiplier = resolution_multipliers.get(resolution, base_multiplier)
    return file_duration * multiplier


def check_disk_space(path: str, required_bytes: int) -> bool:
    """Check if there's enough disk space."""
    try:
        stat = os.statvfs(path)
        free_bytes = stat.f_bavail * stat.f_frsize
        return free_bytes >= required_bytes
    except OSError:
        return False


def get_system_info() -> Dict[str, Any]:
    """Get system information for debugging."""
    info = {
        'cpu_count': os.cpu_count(),
        'platform': os.name,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }
    
    try:
        # Try to get Intel Quick Sync info
        result = subprocess.run(['vainfo'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            info['intel_quicksync'] = 'Intel Quick Sync available' in result.stdout
        else:
            info['intel_quicksync'] = False
    except Exception:
        info['intel_quicksync'] = False
    
    return info
