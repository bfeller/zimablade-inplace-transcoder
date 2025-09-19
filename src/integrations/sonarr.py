"""
Sonarr API integration for updating TV show file paths.
"""

import requests
import logging
from typing import Optional, Dict, Any
from ..utils.config import Config


class SonarrClient:
    """Client for Sonarr API integration."""
    
    def __init__(self, config: Config):
        """Initialize Sonarr client."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.base_url = config.sonarr_url.rstrip('/')
        self.api_key = config.sonarr_api_key
        self.timeout = 30
        
        # Validate configuration
        if not self.api_key:
            raise ValueError("Sonarr API key is required")
    
    def update_file_path(self, old_path: str, new_filename: str) -> bool:
        """Update file path in Sonarr database."""
        try:
            # Find the episode file ID
            episode_file_id = self._find_episode_file_id(old_path)
            if not episode_file_id:
                self.logger.warning("Could not find episode file ID for: %s", old_path)
                return False
            
            # Update the file path
            return self._update_episode_file_path(episode_file_id, new_filename)
            
        except Exception as e:
            self.logger.error("Failed to update Sonarr file path: %s", e)
            return False
    
    def _find_episode_file_id(self, file_path: str) -> Optional[int]:
        """Find episode file ID by file path."""
        try:
            url = f"{self.base_url}/api/v3/episodefile"
            params = {'relativePath': file_path}
            headers = {'X-Api-Key': self.api_key}
            
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            episode_files = response.json()
            if episode_files:
                return episode_files[0]['id']
            
            return None
            
        except requests.RequestException as e:
            self.logger.error("Failed to find episode file ID: %s", e)
            return None
    
    def _update_episode_file_path(self, episode_file_id: int, new_filename: str) -> bool:
        """Update episode file path in Sonarr."""
        try:
            # Get current episode file data
            url = f"{self.base_url}/api/v3/episodefile/{episode_file_id}"
            headers = {'X-Api-Key': self.api_key}
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            episode_file_data = response.json()
            
            # Update the relative path
            episode_file_data['relativePath'] = new_filename
            
            # Send update
            response = requests.put(url, json=episode_file_data, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            self.logger.info("Updated Sonarr episode file path: %s", new_filename)
            return True
            
        except requests.RequestException as e:
            self.logger.error("Failed to update episode file path: %s", e)
            return False
    
    def refresh_series(self, series_id: int) -> bool:
        """Trigger series refresh in Sonarr."""
        try:
            url = f"{self.base_url}/api/v3/command"
            headers = {'X-Api-Key': self.api_key}
            data = {
                'name': 'RescanSeries',
                'seriesId': series_id
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            self.logger.info("Triggered Sonarr series refresh for series ID: %d", series_id)
            return True
            
        except requests.RequestException as e:
            self.logger.error("Failed to refresh Sonarr series: %s", e)
            return False
    
    def get_series_info(self, series_id: int) -> Optional[Dict[str, Any]]:
        """Get series information from Sonarr."""
        try:
            url = f"{self.base_url}/api/v3/series/{series_id}"
            headers = {'X-Api-Key': self.api_key}
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            self.logger.error("Failed to get series info: %s", e)
            return None
    
    def test_connection(self) -> bool:
        """Test connection to Sonarr API."""
        try:
            url = f"{self.base_url}/api/v3/system/status"
            headers = {'X-Api-Key': self.api_key}
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            self.logger.info("Sonarr connection test successful")
            return True
            
        except requests.RequestException as e:
            self.logger.error("Sonarr connection test failed: %s", e)
            return False
