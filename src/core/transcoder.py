"""
Transcoder module using FFmpeg with Intel Quick Sync.
"""

import os
import logging
import subprocess
from pathlib import Path
from typing import Optional

# Debug: Confirm this module is being loaded
print("🚀🚀🚀 TRANSCODER MODULE LOADED - VERSION 0.4.7 🚀🚀🚀")


class Transcoder:
    """Handles video transcoding using FFmpeg with Intel Quick Sync."""
    
    def __init__(self, config):
        """Initialize the transcoder."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Test Intel Quick Sync availability
        self._test_intel_quicksync()
        
        # FFmpeg command template - Intel Quick Sync with proper device initialization
        self.ffmpeg_cmd = [
            'ffmpeg',
            '-init_hw_device', 'qsv=hw',  # Initialize QSV hardware device
            '-filter_hw_device', 'hw',  # Use QSV hardware device for filters
            '-hwaccel', 'qsv',  # Intel Quick Sync hardware acceleration
            '-i', '',  # Input file (will be filled in)
            '-vf', 'hwupload=extra_hw_frames=64,format=qsv,scale_qsv=1920:1080',  # Upload to QSV and scale
            '-c:v', 'h264_qsv',  # H.264 encoder using QSV
            '-preset', 'medium',  # Encoding preset
            '-crf', str(self.config.crf_quality),  # Quality setting
            '-c:a', 'aac',  # AAC audio codec
            '-b:a', f'{self.config.audio_bitrate}k',  # Audio bitrate
            '-c:s', 'copy',  # Copy subtitles as-is (don't convert)
            '-map', '0:v:0',  # Map video stream
            '-map', '0:a:m:language:eng?',  # Map English audio if available, fallback to first audio
            '-map', '0:s',  # Map all subtitle streams
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
                    # Test with proper QSV initialization (our actual approach)
                    device_test = subprocess.run(['ffmpeg', '-init_hw_device', 'qsv=hw', '-filter_hw_device', 'hw',
                                                '-f', 'lavfi', '-i', 'testsrc=duration=0.1:size=1920x1080:rate=1',
                                                '-vf', 'hwupload=extra_hw_frames=64,format=qsv,scale_qsv=1280:720', 
                                                '-c:v', 'h264_qsv', '-f', 'null', '-'],
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
            '-c:s', 'mov_text',  # Convert subtitles to MP4-compatible format
            '-map', '0:v:0',  # Map video stream
            '-map', '0:a:m:language:eng?',  # Map English audio if available, fallback to first audio
            '-map', '0:s:0',  # Map only the first subtitle stream (English)
            '-map', '0:s:1',  # Map the second subtitle stream (English SDH)
            '-y',  # Overwrite output file
            ''  # Output file (will be filled in)
        ]
    
    def transcode(self, input_path: str, output_path: str, original_path: str = None) -> bool:
        """Transcode a video file from input to output with automatic fallback."""
        print("🚀🚀🚀 TRANSCODE METHOD CALLED - VERSION 0.3.4 🚀🚀🚀")
        print("🔥🔥🔥 TESTING LOGGER - THIS SHOULD APPEAR 🔥🔥🔥")
        self.logger.info("🚀🚀🚀 VERSION 0.3.4 DEPLOYED - TRANSCODE METHOD STARTED 🚀🚀🚀")
        self.logger.info("🔥🔥🔥 CACHE BUSTING - THIS WILL DEFINITELY WORK 🔥🔥🔥")
        self.logger.error("🚨🚨🚨 ERROR LEVEL TEST - THIS SHOULD DEFINITELY APPEAR 🚨🚨🚨")
        self.logger.info("Transcoder.transcode() called with input_path=%s, output_path=%s, original_path=%s", 
                        input_path, output_path, original_path)
        
        try:
            print("🔥🔥🔥 STARTING TRANSCODING PROCESS 🔥🔥🔥")
            self.logger.info("Starting transcoding: %s -> %s", input_path, output_path)
            
            # Validate input file
            if not os.path.exists(input_path):
                self.logger.error("Input file does not exist: %s", input_path)
                return False
            
            # Create output directory if it doesn't exist
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Try Intel Quick Sync first
            print("🚀🚀🚀 ATTEMPTING INTEL QUICK SYNC 🚀🚀🚀")
            self.logger.info("Attempting Intel Quick Sync transcoding...")
            self.logger.info("Intel Quick Sync attempt starting...")
            success = self._transcode_with_current_settings(input_path, output_path)
            
            if success:
                print("✅✅✅ INTEL QUICK SYNC SUCCESS ✅✅✅")
                self.logger.info("Intel Quick Sync transcoding successful!")
                return True
            
            # Intel Quick Sync failed, try software encoding
            print("⚠️⚠️⚠️ INTEL QUICK SYNC FAILED - FALLING BACK TO SOFTWARE ⚠️⚠️⚠️")
            self.logger.warning("Intel Quick Sync failed, falling back to software encoding...")
            self.logger.info("Switching to software encoding configuration...")
            self._fallback_to_software()
            self.logger.info("Software encoding configuration applied, starting transcoding...")
            self.logger.info("Software encoding attempt starting...")
            print("🔥🔥🔥 STARTING SOFTWARE ENCODING ATTEMPT 🔥🔥🔥")
            success = self._transcode_with_current_settings(input_path, output_path)
            
            if success:
                print("✅✅✅ SOFTWARE ENCODING SUCCESS ✅✅✅")
                self.logger.info("Software encoding transcoding successful!")
                return True
            else:
                print("❌❌❌ BOTH ENCODING METHODS FAILED ❌❌❌")
                self.logger.error("Both Intel Quick Sync and software encoding failed")
                return False
                       
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
                self.logger.warning("ffprobe return code: %d", result.returncode)
                self.logger.warning("ffprobe stdout: %s", result.stdout)
                return False
                
        except Exception as e:
            self.logger.warning("Error checking for HDR content: %s", e)
            return False
    
    def _transcode_with_current_settings(self, input_path: str, output_path: str) -> bool:
        """Transcode using current FFmpeg settings."""
        try:
            self.logger.info("Building FFmpeg command...")
            # Build FFmpeg command
            cmd = self._build_command(input_path, output_path)
            
            # Log the exact command for debugging
            self.logger.info("Running FFmpeg command: %s", ' '.join(cmd))
            self.logger.info("Starting FFmpeg process...")
            
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
        
        # Find the -i flag and set the input file after it
        for i, arg in enumerate(cmd):
            if arg == '-i':
                cmd[i + 1] = input_path
                break
        
        cmd[-1] = output_path  # Set output file
        return cmd
    
    def _run_ffmpeg(self, cmd: list) -> bool:
        """Run FFmpeg command and return success status."""
        try:
            self.logger.debug("Running FFmpeg command: %s", ' '.join(cmd))
            self.logger.info("Launching FFmpeg subprocess...")
            
            # Run FFmpeg with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            self.logger.info("FFmpeg subprocess launched, PID: %d", process.pid)
            self.logger.info("Starting progress monitoring...")
            
            # Monitor progress with timeout
            self._monitor_progress(process)
            
            self.logger.info("FFmpeg process completed, waiting for final return code...")
            # Wait for completion with timeout (30 minutes max)
            try:
                return_code = process.wait(timeout=1800)  # 30 minutes timeout
            except subprocess.TimeoutExpired:
                self.logger.error("FFmpeg process timed out after 30 minutes - killing process")
                process.kill()
                return False
            
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
                        # Log progress every 10 seconds to provide better feedback
                        import time
                        current_time = time.time()
                        if current_time - last_progress_time >= 10:
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
