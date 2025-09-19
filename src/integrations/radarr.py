"""
Radarr API integration for updating movie file paths.
"""

import requests
import logging
from typing import Optional, Dict, Any
from ..utils.config import Config


class RadarrClient:
    """Client for Radarr API integration."""
    
    def __init__(self, config: Config):
        """Initialize Radarr client."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.base_url = config.radarr_url.rstrip('/')
        self.api_key = config.radarr_api_key
        self.timeout = 30
        
        # Validate configuration
        if not self.api_key:
            raise ValueError("Radarr API key is required")
    
    def update_file_path(self, old_path: str, new_filename: str) -> bool:
        """Update file path in Radarr database."""
        try:
            # Find the movie file ID
            movie_file_id = self._find_movie_file_id(old_path)
            if not movie_file_id:
                self.logger.warning("Could not find movie file ID for: %s", old_path)
                return False
            
            # Update the file path
            return self._update_movie_file_path(movie_file_id, new_filename)
            
        except Exception as e:
            self.logger.error("Failed to update Radarr file path: %s", e)
            return False
    
    def _find_movie_file_id(self, file_path: str) -> Optional[int]:
        """Find movie file ID by file path."""
        try:
            url = f"{self.base_url}/api/v3/moviefile"
            params = {'relativePath': file_path}
            headers = {'X-Api-Key': self.api_key}
            
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            movie_files = response.json()
            if movie_files:
                return movie_files[0]['id']
            
            return None
            
        except requests.RequestException as e:
            self.logger.error("Failed to find movie file ID: %s", e)
            return None
    
    def _update_movie_file_path(self, movie_file_id: int, new_filename: str) -> bool:
        """Update movie file path in Radarr."""
        try:
            # Get current movie file data
            url = f"{self.base_url}/api/v3/moviefile/{movie_file_id}"
            headers = {'X-Api-Key': self.api_key}
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            movie_file_data = response.json()
            
            # Update the relative path
            movie_file_data['relativePath'] = new_filename
            
            # Send update
            response = requests.put(url, json=movie_file_data, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            self.logger.info("Updated Radarr movie file path: %s", new_filename)
            return True
            
        except requests.RequestException as e:
            self.logger.error("Failed to update movie file path: %s", e)
            return False
    
    def refresh_movie(self, movie_id: int) -> bool:
        """Trigger movie refresh in Radarr."""
        try:
            url = f"{self.base_url}/api/v3/command"
            headers = {'X-Api-Key': self.api_key}
            data = {
                'name': 'RescanMovie',
                'movieId': movie_id
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            self.logger.info("Triggered Radarr movie refresh for movie ID: %d", movie_id)
            return True
            
        except requests.RequestException as e:
            self.logger.error("Failed to refresh Radarr movie: %s", e)
            return False
    
    def get_movie_info(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Get movie information from Radarr."""
        try:
            url = f"{self.base_url}/api/v3/movie/{movie_id}"
            headers = {'X-Api-Key': self.api_key}
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            self.logger.error("Failed to get movie info: %s", e)
            return None
    
    def test_connection(self) -> bool:
        """Test connection to Radarr API."""
        try:
            url = f"{self.base_url}/api/v3/system/status"
            headers = {'X-Api-Key': self.api_key}
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            self.logger.info("Radarr connection test successful")
            return True
            
        except requests.RequestException as e:
            self.logger.error("Radarr connection test failed: %s", e)
            return False
