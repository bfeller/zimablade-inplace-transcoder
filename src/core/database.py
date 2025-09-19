"""
Database module for tracking processed files.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List


class Database:
    """SQLite database for tracking processed files."""
    
    def __init__(self, db_path: str):
        """Initialize database connection."""
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.connection = None
    
    def initialize(self):
        """Initialize database and create tables."""
        try:
            # Ensure database directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            
            # Create tables
            self._create_tables()
            
            self.logger.info("Database initialized: %s", self.db_path)
            
        except Exception as e:
            self.logger.error("Failed to initialize database: %s", e)
            raise
    
    def _create_tables(self):
        """Create database tables."""
        cursor = self.connection.cursor()
        
        # File analysis cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_analysis_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_size INTEGER NOT NULL,
                file_mtime REAL NOT NULL,
                duration_seconds REAL,
                width INTEGER,
                height INTEGER,
                codec TEXT,
                bitrate INTEGER,
                needs_transcoding BOOLEAN NOT NULL,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Processed files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_path TEXT UNIQUE NOT NULL,
                output_filename TEXT NOT NULL,
                original_size INTEGER NOT NULL,
                output_size INTEGER,
                duration_seconds REAL,
                width INTEGER,
                height INTEGER,
                codec TEXT,
                bitrate INTEGER,
                is_tv_show BOOLEAN NOT NULL,
                is_movie BOOLEAN NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processing_time_seconds INTEGER,
                status TEXT DEFAULT 'completed',
                error_message TEXT
            )
        ''')
        
        # Processing statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                files_processed INTEGER DEFAULT 0,
                total_size_saved INTEGER DEFAULT 0,
                total_processing_time INTEGER DEFAULT 0,
                avg_processing_time REAL DEFAULT 0,
                success_rate REAL DEFAULT 0
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_original_path ON processed_files(original_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_processed_at ON processed_files(processed_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON processing_stats(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_path ON file_analysis_cache(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyzed_at ON file_analysis_cache(analyzed_at)')
        
        self.connection.commit()
        self.logger.debug("Database tables created successfully")
    
    def get_cached_analysis(self, file_path: str, file_size: int, file_mtime: float) -> Optional[dict]:
        """Get cached file analysis if file hasn't changed."""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM file_analysis_cache 
                WHERE file_path = ? AND file_size = ? AND file_mtime = ?
            ''', (str(file_path), file_size, file_mtime))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            self.logger.error("Error getting cached analysis: %s", e)
            return None
    
    def cache_analysis(self, file_path: str, file_size: int, file_mtime: float, 
                      analysis_result: dict, needs_transcoding: bool):
        """Cache file analysis results."""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO file_analysis_cache 
                (file_path, file_size, file_mtime, duration_seconds, width, height, 
                 codec, bitrate, needs_transcoding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(file_path),
                file_size,
                file_mtime,
                analysis_result.get('duration', 0),
                analysis_result.get('width', 0),
                analysis_result.get('height', 0),
                analysis_result.get('codec', 'unknown'),
                analysis_result.get('bitrate', 0),
                needs_transcoding
            ))
            
            self.connection.commit()
            self.logger.debug("Cached analysis for: %s", file_path)
            
        except Exception as e:
            self.logger.error("Error caching analysis: %s", e)
    
    def is_file_processed(self, file_path: str) -> bool:
        """Check if a file has already been processed."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                'SELECT id FROM processed_files WHERE original_path = ?',
                (str(file_path),)
            )
            result = cursor.fetchone()
            return result is not None
            
        except Exception as e:
            self.logger.error("Error checking if file is processed: %s", e)
            return False
    
    def mark_as_processed(self, original_path: str, output_filename: str, 
                         file_info: dict, processing_time: int = None, 
                         status: str = 'completed', error_message: str = None):
        """Mark a file as processed in the database."""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO processed_files 
                (original_path, output_filename, original_size, output_size,
                 duration_seconds, width, height, codec, bitrate,
                 is_tv_show, is_movie, processing_time_seconds, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(original_path),
                output_filename,
                file_info.get('size_bytes', 0),
                file_info.get('output_size', 0),
                file_info.get('duration_seconds', 0),
                file_info.get('width', 0),
                file_info.get('height', 0),
                file_info.get('codec', 'unknown'),
                file_info.get('bitrate', 0),
                file_info.get('is_tv_show', False),
                file_info.get('is_movie', False),
                processing_time,
                status,
                error_message
            ))
            
            self.connection.commit()
            self.logger.debug("Marked file as processed: %s", original_path)
            
        except Exception as e:
            self.logger.error("Error marking file as processed: %s", e)
            raise
    
    def get_processing_stats(self, days: int = 30) -> List[dict]:
        """Get processing statistics for the last N days."""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT 
                    DATE(processed_at) as date,
                    COUNT(*) as files_processed,
                    SUM(original_size - COALESCE(output_size, original_size)) as size_saved,
                    SUM(processing_time_seconds) as total_time,
                    AVG(processing_time_seconds) as avg_time,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                FROM processed_files 
                WHERE processed_at >= datetime('now', '-{} days')
                GROUP BY DATE(processed_at)
                ORDER BY date DESC
            '''.format(days))
            
            results = []
            for row in cursor.fetchall():
                results.append(dict(row))
            
            return results
            
        except Exception as e:
            self.logger.error("Error getting processing stats: %s", e)
            return []
    
    def get_file_history(self, file_path: str) -> Optional[dict]:
        """Get processing history for a specific file."""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT * FROM processed_files 
                WHERE original_path = ?
                ORDER BY processed_at DESC
                LIMIT 1
            ''', (str(file_path),))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            self.logger.error("Error getting file history: %s", e)
            return None
    
    def cleanup_old_records(self, days: int = 90):
        """Clean up old processing records."""
        try:
            cursor = self.connection.cursor()
            
            # Delete old processed files records
            cursor.execute('''
                DELETE FROM processed_files 
                WHERE processed_at < datetime('now', '-{} days')
            '''.format(days))
            
            deleted_count = cursor.rowcount
            
            # Delete old statistics
            cursor.execute('''
                DELETE FROM processing_stats 
                WHERE date < date('now', '-{} days')
            '''.format(days))
            
            self.connection.commit()
            
            if deleted_count > 0:
                self.logger.info("Cleaned up %d old database records", deleted_count)
            
        except Exception as e:
            self.logger.error("Error cleaning up old records: %s", e)
    
    def clear_all_data(self):
        """Clear all data from the database (for testing/reset purposes)."""
        try:
            cursor = self.connection.cursor()
            
            # Clear processed files table
            cursor.execute('DELETE FROM processed_files')
            processed_count = cursor.rowcount
            
            # Clear file analysis cache
            cursor.execute('DELETE FROM file_analysis_cache')
            cache_count = cursor.rowcount
            
            # Clear processing stats
            cursor.execute('DELETE FROM processing_stats')
            stats_count = cursor.rowcount
            
            self.connection.commit()
            
            self.logger.warning("CLEARED ALL DATABASE DATA:")
            self.logger.warning("  - %d processed files records deleted", processed_count)
            self.logger.warning("  - %d analysis cache records deleted", cache_count)
            self.logger.warning("  - %d processing stats records deleted", stats_count)
            
        except Exception as e:
            self.logger.error("Error clearing database: %s", e)
            raise
    
    def get_database_stats(self) -> dict:
        """Get database statistics for debugging."""
        try:
            cursor = self.connection.cursor()
            
            # Count processed files
            cursor.execute('SELECT COUNT(*) as count FROM processed_files')
            processed_count = cursor.fetchone()['count']
            
            # Count completed vs failed
            cursor.execute('SELECT status, COUNT(*) as count FROM processed_files GROUP BY status')
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Count cached analysis
            cursor.execute('SELECT COUNT(*) as count FROM file_analysis_cache')
            cache_count = cursor.fetchone()['count']
            
            return {
                'processed_files': processed_count,
                'status_counts': status_counts,
                'cached_analysis': cache_count
            }
            
        except Exception as e:
            self.logger.error("Error getting database stats: %s", e)
            return {}
    
    def clear_failed_files(self):
        """Clear records of files that failed processing."""
        try:
            cursor = self.connection.cursor()
            
            # Delete failed processing records
            cursor.execute('DELETE FROM processed_files WHERE status != "completed"')
            failed_count = cursor.rowcount
            
            self.connection.commit()
            
            if failed_count > 0:
                self.logger.info("Cleared %d failed file records from database", failed_count)
            
        except Exception as e:
            self.logger.error("Error clearing failed files: %s", e)
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.logger.debug("Database connection closed")
