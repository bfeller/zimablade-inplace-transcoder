# Zimablade Transcoder - Directory Structure

## Project Layout

```
zimablade-inplace-transcoder/
├── README.md                           # Project documentation
├── DIRECTORY_STRUCTURE.md              # This file
├── docker-compose.yml                  # Docker deployment configuration
├── Dockerfile                          # Container build instructions
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment variables template
├── .gitignore                          # Git ignore rules
│
├── src/                                # Source code
│   ├── __init__.py
│   ├── main.py                         # Main application entry point
│   │
│   ├── core/                           # Core business logic
│   │   ├── __init__.py
│   │   ├── scanner.py                  # File scanning and detection
│   │   ├── transcoder.py               # FFmpeg transcoding logic
│   │   ├── file_manager.py             # File operations and management
│   │   └── database.py                 # SQLite database operations
│   │
│   ├── integrations/                   # External service integrations
│   │   ├── __init__.py
│   │   ├── sonarr.py                   # Sonarr API integration
│   │   ├── radarr.py                   # Radarr API integration
│   │   └── base.py                     # Base API client
│   │
│   ├── utils/                          # Utility functions
│   │   ├── __init__.py
│   │   ├── logging.py                  # Logging configuration
│   │   ├── config.py                   # Configuration management
│   │   ├── helpers.py                  # General helper functions
│   │   └── validators.py               # Input validation
│   │
│   └── models/                         # Data models
│       ├── __init__.py
│       ├── file_info.py                # File information model
│       ├── transcoding_job.py          # Transcoding job model
│       └── api_response.py             # API response models
│
├── config/                             # Configuration files
│   ├── logging.yaml                    # Logging configuration
│   ├── transcoding.yaml                # Transcoding parameters
│   └── sonarr_radarr.yaml              # API configuration
│
├── scripts/                            # Utility scripts
│   ├── setup.sh                        # Initial setup script
│   ├── test_transcoding.sh             # Test transcoding functionality
│   └── cleanup.sh                      # Cleanup script
│
├── docs/                               # Documentation
│   ├── api.md                          # API documentation
│   ├── deployment.md                   # Deployment guide
│   ├── troubleshooting.md              # Troubleshooting guide
│   └── examples/                       # Usage examples
│
└── data/                               # Runtime data (created at runtime)
    ├── database/                       # SQLite database files
    │   ├── transcoding.db              # Main database
    │   └── backups/                     # Database backups
    ├── logs/                           # Application logs
    │   ├── transcoder.log              # Main log file
    │   ├── scanner.log                 # Scanner specific logs
    │   └── archived/                   # Archived logs
    └── temp/                           # Temporary files
        ├── working/                    # Active transcoding files
        ├── completed/                  # Successfully processed files
        └── failed/                     # Failed transcoding files
```

## Directory Responsibilities

### `/src/` - Source Code
- **`main.py`**: Application entry point, CLI interface, main loop
- **`core/`**: Core business logic, independent of external services
- **`integrations/`**: External service integrations (Sonarr, Radarr)
- **`utils/`**: Reusable utility functions and configurations
- **`models/`**: Data models and structures

### `/config/` - Configuration Files
- **`logging.yaml`**: Logging levels, formats, rotation settings
- **`transcoding.yaml`**: FFmpeg parameters, quality settings
- **`sonarr_radarr.yaml`**: API endpoints, authentication

### `/scripts/` - Utility Scripts
- **`setup.sh`**: Initial environment setup
- **`test_transcoding.sh`**: Test transcoding with sample files
- **`cleanup.sh`**: Clean up temporary files and logs


### `/docs/` - Documentation
- **API documentation** for external integrations
- **Deployment guides** for Docker setup
- **Troubleshooting** common issues

### `/data/` - Runtime Data (Created at Runtime)
- **`database/`**: SQLite databases and backups
- **`logs/`**: Application logs with rotation
- **`temp/`**: Temporary files during processing

## Key Design Principles

### 1. **Separation of Concerns**
- **Scanner**: Only handles file detection and analysis
- **Transcoder**: Only handles FFmpeg operations
- **File Manager**: Only handles file operations
- **Integrations**: Only handle external API calls

### 2. **Dependency Injection**
- Configuration passed to modules
- No hardcoded paths or settings
- Easy to test and mock

### 3. **Error Handling**
- Each module handles its own errors
- Centralized error logging
- Graceful degradation

### 4. **Configuration Management**
- Environment variables for sensitive data
- YAML files for complex configurations
- Clear separation of dev/prod settings


## File Naming Conventions

### Python Files
- **`snake_case.py`** for modules and files
- **`PascalCase`** for classes
- **`snake_case`** for functions and variables
- **`UPPER_CASE`** for constants

### Configuration Files
- **`snake_case.yaml`** for YAML configs
- **`snake_case.env`** for environment files
- **`PascalCase.md`** for documentation

### Data Files
- **`snake_case.db`** for databases
- **`snake_case.log`** for log files
- **`snake_case.tmp`** for temporary files

## Benefits of This Structure

1. **Maintainability**: Clear separation makes code easy to understand and modify
2. **Scalability**: Easy to add new features or integrations
3. **Deployment**: Clear separation of code, config, and data
4. **Debugging**: Logs and data are organized and easy to find
5. **Documentation**: Self-documenting structure with clear responsibilities
