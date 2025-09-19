"""
Transcoder module using FFmpeg with Intel Quick Sync.
"""

import os
import logging
import subprocess
from pathlib import Path
from typing import Optional


class Transcoder:
    """Handles video transcoding using FFmpeg with Intel Quick Sync."""
    
    def __init__(self, config):
        """Initialize the transcoder."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Test Intel Quick Sync availability
        self._test_intel_quicksync()
        
        # FFmpeg command template - use hybrid approach for better compatibility
        self.ffmpeg_cmd = [
            'ffmpeg',
            '-hwaccel', 'qsv',  # Intel Quick Sync hardware acceleration
            '-i', '',  # Input file (will be filled in)
            '-vf', 'scale=1920:1080',  # Scale to 1080p using software (more compatible)
            '-c:v', 'h264_qsv',  # H.264 encoder using QSV
            '-preset', 'medium',  # Encoding preset
            '-crf', str(self.config.crf_quality),  # Quality setting
            '-c:a', 'aac',  # AAC audio codec
            '-b:a', f'{self.config.audio_bitrate}k',  # Audio bitrate
            '-c:s', 'mov_text',  # Subtitle codec for MP4
            '-map', '0',  # Map all streams
            '-y',  # Overwrite output file
            ''  # Output file (will be filled in)
        ]
    
    def _test_intel_quicksync(self):
        """Test if Intel Quick Sync is available."""
        try:
            # Test if QSV encoders are available
            result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True, timeout=10)
            if 'h264_qsv' in result.stdout:
                self.logger.info("Intel Quick Sync H.264 encoder is available")
                
                # Test device access with realistic scenario
                try:
                    # Test with software scaling + QSV encoding (our actual approach)
                    device_test = subprocess.run(['ffmpeg', '-hwaccel', 'qsv', '-f', 'lavfi', '-i', 'testsrc=duration=0.1:size=1920x1080:rate=1', 
                                                '-vf', 'scale=1280:720', '-c:v', 'h264_qsv', '-f', 'null', '-'], 
                                               capture_output=True, text=True, timeout=15)
                    if device_test.returncode == 0:
                        self.logger.info("Intel Quick Sync device access test successful")
                    else:
                        self.logger.warning("Intel Quick Sync device access failed: %s", device_test.stderr[:200] if device_test.stderr else "Unknown error")
                        self.logger.info("Falling back to software encoding")
                        self._fallback_to_software()
                except Exception as e:
                    self.logger.warning("Intel Quick Sync device test failed: %s", e)
                    self.logger.info("Falling back to software encoding")
                    self._fallback_to_software()
            else:
                self.logger.warning("Intel Quick Sync H.264 encoder not found, falling back to software encoding")
                self._fallback_to_software()
        except Exception as e:
            self.logger.warning("Could not test Intel Quick Sync availability: %s", e)
            self._fallback_to_software()
    
    def _fallback_to_software(self):
        """Fallback to software encoding."""
        self.logger.info("Using software encoding fallback")
        self.ffmpeg_cmd = [
            'ffmpeg',
            '-i', '',  # Input file (will be filled in)
            '-vf', 'scale=1920:1080',  # Scale to 1080p using software
            '-c:v', 'libx264',  # Software H.264 encoder
            '-preset', 'medium',  # Encoding preset
            '-crf', str(self.config.crf_quality),  # Quality setting
            '-c:a', 'aac',  # AAC audio codec
            '-b:a', f'{self.config.audio_bitrate}k',  # Audio bitrate
            '-c:s', 'mov_text',  # Subtitle codec for MP4
            '-map', '0',  # Map all streams
            '-y',  # Overwrite output file
            ''  # Output file (will be filled in)
        ]
    
    def transcode(self, input_path: str, output_path: str, original_path: str = None) -> bool:
        """Transcode a video file from input to output."""
        self.logger.info("Transcoder.transcode() called with input_path=%s, output_path=%s, original_path=%s", 
                        input_path, output_path, original_path)
        
        try:
            self.logger.info("Starting transcoding: %s -> %s", input_path, output_path)
            
            # Validate input file
            if not os.path.exists(input_path):
                self.logger.error("Input file does not exist: %s", input_path)
                return False
            
            # Create output directory if it doesn't exist
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if file has HDR/Dolby Vision content that might not work with QSV
            # Use original_path for detection if provided, otherwise use input_path
            detection_path = original_path if original_path else input_path
            self.logger.info("Checking file for HDR/10-bit content: %s", detection_path)
            
            try:
                has_hdr = self._has_hdr_content(detection_path)
                self.logger.info("HDR/10-bit detection result: %s", has_hdr)
            except Exception as e:
                self.logger.error("Error during HDR detection: %s", e, exc_info=True)
                has_hdr = False  # Default to QSV if detection fails
            
            if has_hdr:
                self.logger.info("File contains HDR/Dolby Vision content - using software encoding for better compatibility")
                # Temporarily switch to software encoding for this file
                original_cmd = self.ffmpeg_cmd.copy()
                self._fallback_to_software()
                success = self._transcode_with_current_settings(input_path, output_path)
                # Restore original command
                self.ffmpeg_cmd = original_cmd
                return success
            else:
                self.logger.info("File appears compatible with Intel Quick Sync - using hardware acceleration")
                # Use current settings (QSV if available)
                return self._transcode_with_current_settings(input_path, output_path)
                       
        except Exception as e:
            self.logger.error("Transcoding error: %s", e, exc_info=True)
            return False
    
    def _has_hdr_content(self, input_path: str) -> bool:
        """Check if file contains HDR/Dolby Vision content."""
        self.logger.info("_has_hdr_content() called with path: %s", input_path)
        
        try:
            # Use ffprobe to check for HDR metadata
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(input_path)  # Convert PosixPath to string
            ]
            
            self.logger.info("Running ffprobe command: %s", ' '.join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                # Check stream metadata for HDR and 10-bit content
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        # Check for 10-bit HEVC (often problematic with QSV)
                        codec_name = stream.get('codec_name', '').lower()
                        pix_fmt = stream.get('pix_fmt', '').lower()
                        
                        self.logger.info("Video stream: codec=%s, pix_fmt=%s", codec_name, pix_fmt)
                        
                        # Check for 10-bit content (most reliable indicator of QSV issues)
                        if '10' in pix_fmt:
                            self.logger.info("10-bit content detected - using software encoding for better compatibility")
                            return True
                        
                        # Check for HDR metadata
                        side_data = stream.get('side_data_list', [])
                        for side_data_item in side_data:
                            if side_data_item.get('side_data_type') in ['Mastering display metadata', 'Content light level metadata']:
                                self.logger.info("HDR metadata found in stream")
                                return True
                        
                        # Check for Dolby Vision
                        if 'dolby' in str(stream.get('tags', {})).lower():
                            self.logger.info("Dolby Vision metadata found")
                            return True
                
                self.logger.info("No HDR/10-bit content detected - file should work with Intel Quick Sync")
                return False
            else:
                self.logger.warning("Could not analyze file for HDR content: %s", result.stderr)
                return False
                
        except Exception as e:
            self.logger.warning("Error checking for HDR content: %s", e)
            return False
    
    def _transcode_with_current_settings(self, input_path: str, output_path: str) -> bool:
        """Transcode using current FFmpeg settings."""
        try:
            # Build FFmpeg command
            cmd = self._build_command(input_path, output_path)
            
            # Log the exact command for debugging
            self.logger.info("Running FFmpeg command: %s", ' '.join(cmd))
            
            # Run FFmpeg
            result = self._run_ffmpeg(cmd)
            
            if result:
                self.logger.info("Transcoding completed successfully: %s", output_path)
                return True
            else:
                self.logger.error("Transcoding failed: %s", input_path)
                return False
                
        except Exception as e:
            self.logger.error("Transcoding error: %s", e, exc_info=True)
            return False
    
    def _build_command(self, input_path: str, output_path: str) -> list:
        """Build the FFmpeg command with input and output paths."""
        cmd = self.ffmpeg_cmd.copy()
        cmd[4] = input_path  # Set input file (after -i flag)
        cmd[-1] = output_path  # Set output file
        return cmd
    
    def _run_ffmpeg(self, cmd: list) -> bool:
        """Run FFmpeg command and return success status."""
        try:
            self.logger.debug("Running FFmpeg command: %s", ' '.join(cmd))
            
            # Run FFmpeg with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # Monitor progress
            self._monitor_progress(process)
            
            # Wait for completion
            return_code = process.wait()
            
            if return_code == 0:
                self.logger.info("FFmpeg completed successfully")
                return True
            else:
                # Get stored stderr lines from progress monitoring
                stderr_lines = getattr(process, '_stderr_lines', [])
                stdout_output = process.stdout.read()
                
                self.logger.error("FFmpeg failed with return code %d", return_code)
                if stderr_lines:
                    self.logger.error("FFmpeg stderr:")
                    for line in stderr_lines:
                        self.logger.error("  %s", line)
                else:
                    self.logger.error("No stderr output captured")
                
                if stdout_output:
                    self.logger.error("FFmpeg stdout: %s", stdout_output)
                
                # Check if this is an Intel Quick Sync initialization error
                if any('Error initializing an internal MFX session' in line for line in stderr_lines):
                    self.logger.warning("Intel Quick Sync initialization failed - this may be due to unsupported video format (HDR/DV)")
                    self.logger.info("Consider using software encoding for this file type")
                
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("FFmpeg command timed out")
            process.kill()
            return False
        except Exception as e:
            self.logger.error("Error running FFmpeg: %s", e)
            return False
    
    def _monitor_progress(self, process):
        """Monitor FFmpeg progress and log updates."""
        try:
            last_progress_time = 0
            stderr_lines = []
            
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                
                # Store all stderr lines for error reporting
                stderr_lines.append(line.strip())
                
                # Parse progress information
                if 'frame=' in line and 'fps=' in line:
                    # Extract frame and fps info
                    parts = line.strip().split()
                    frame_info = next((p for p in parts if p.startswith('frame=')), '')
                    fps_info = next((p for p in parts if p.startswith('fps=')), '')
                    time_info = next((p for p in parts if p.startswith('time=')), '')
                    speed_info = next((p for p in parts if p.startswith('speed=')), '')
                    bitrate_info = next((p for p in parts if p.startswith('bitrate=')), '')
                    
                    if frame_info and fps_info:
                        # Log progress every 30 seconds to avoid spam
                        import time
                        current_time = time.time()
                        if current_time - last_progress_time >= 30:
                            self.logger.info("Transcoding Progress: %s %s %s %s %s", 
                                            frame_info, fps_info, time_info, speed_info, bitrate_info)
                            last_progress_time = current_time
                        else:
                            self.logger.debug("Progress: %s %s %s %s %s", 
                                            frame_info, fps_info, time_info, speed_info, bitrate_info)
                
                # Check for error messages
                elif any(keyword in line.lower() for keyword in ['error', 'failed', 'cannot', 'invalid']):
                    self.logger.error("FFmpeg error detected: %s", line.strip())
            
            # Store stderr lines for later retrieval
            process._stderr_lines = stderr_lines
                        
        except Exception as e:
            self.logger.warning("Error monitoring progress: %s", e)
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
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
                import json
                return json.loads(result.stdout)
            else:
                self.logger.error("ffprobe failed: %s", result.stderr)
                return None
                
        except Exception as e:
            self.logger.error("Error getting file info: %s", e)
            return None
    
    def estimate_transcoding_time(self, input_path: str) -> Optional[int]:
        """Estimate transcoding time in seconds."""
        try:
            # Get file duration
            info = self.get_file_info(input_path)
            if not info:
                return None
            
            duration = float(info.get('format', {}).get('duration', 0))
            
            # Rough estimate: 0.1x realtime for Intel Quick Sync
            # This is a conservative estimate
            estimated_time = int(duration * 0.1)
            
            self.logger.debug("Estimated transcoding time for %s: %d seconds", 
                            input_path, estimated_time)
            return estimated_time
            
        except Exception as e:
            self.logger.warning("Could not estimate transcoding time: %s", e)
            return None
