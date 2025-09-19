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
        
        self.connection.commit()
        self.logger.debug("Database tables created successfully")
    
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
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.logger.debug("Database connection closed")
