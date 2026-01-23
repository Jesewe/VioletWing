import os
import logging
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from typing import Optional, List
import sys
import threading

@dataclass
class LoggerConfig:
    """Configuration for the Logger class."""
    log_directory: str = os.path.expanduser(r'~\AppData\Local\VioletWing\logs')
    max_bytes: int = 5 * 1024 * 1024  # 5MB
    backup_count: int = 5
    clear_on_startup: bool = True
    console_level: int = logging.INFO
    file_level: int = logging.INFO
    detailed_level: int = logging.DEBUG
    suppress_patterns: List[str] = None
    
    def __post_init__(self):
        """Initialize default suppress patterns if none provided."""
        if self.suppress_patterns is None:
            self.suppress_patterns = [
                "Error drawing entity: 'NoneType' object is not subscriptable"
            ]

class SuppressErrorFilter(logging.Filter):
    """A logging filter to suppress messages containing specific patterns."""
    
    def __init__(self, patterns: List[str]):
        """
        Initialize the filter with a list of patterns to suppress.
        
        Args:
            patterns: List of string patterns to suppress in log messages
        """
        super().__init__()
        self.patterns = patterns or []
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Return False if any pattern is found in the message, True otherwise.
        
        Args:
            record: The log record to filter
            
        Returns:
            False if message should be suppressed, True otherwise
        """
        message = record.getMessage()
        return not any(pattern in message for pattern in self.patterns)

class Logger:
    """
    A thread-safe singleton logger for the application.
    
    Features:
    - Rotating log files with configurable size and backup count
    - Separate standard and detailed log files
    - Console logging with customizable filters
    - Thread-safe initialization
    - Configurable via LoggerConfig dataclass
    
    Usage:
        # Basic usage
        logger = Logger.get_logger(__name__)
        logger.info("Application started")
        
        # Custom configuration
        config = LoggerConfig(max_bytes=10*1024*1024, backup_count=10)
        Logger.setup_logging(config)
    """
    
    _config: Optional[LoggerConfig] = None
    _logger: Optional[logging.Logger] = None
    _logger_configured: bool = False
    _lock: threading.Lock = threading.Lock()
    
    @classmethod
    @property
    def LOG_DIRECTORY(cls) -> str:
        """Get the log directory path."""
        return cls._config.log_directory if cls._config else LoggerConfig().log_directory
    
    @classmethod
    @property
    def LOG_FILE(cls) -> str:
        """Get the standard log file path."""
        log_dir = cls._config.log_directory if cls._config else LoggerConfig().log_directory
        return os.path.join(log_dir, 'violetwing.log')
    
    @classmethod
    @property
    def DETAILED_LOG_FILE(cls) -> str:
        """Get the detailed log file path."""
        log_dir = cls._config.log_directory if cls._config else LoggerConfig().log_directory
        return os.path.join(log_dir, 'violetwing_detailed.log')
    
    @staticmethod
    def _clear_existing_logs(log_files: List[str], backup_count: int) -> None:
        """
        Clear existing log files and their backups.
        
        Args:
            log_files: List of log file paths to clear
            backup_count: Number of backup files to remove
        """
        for log_file in log_files:
            try:
                if os.path.exists(log_file):
                    # Clear the main log file
                    with open(log_file, 'w', encoding='utf-8') as f:
                        f.truncate(0)
                    
                    # Remove backup files
                    for i in range(1, backup_count + 1):
                        backup_file = f"{log_file}.{i}"
                        if os.path.exists(backup_file):
                            os.remove(backup_file)
            except (OSError, PermissionError) as e:
                print(f"Warning: Could not clear log file {log_file}: {e}", file=sys.stderr)
            except Exception as e:
                print(f"Unexpected error clearing log file {log_file}: {e}", file=sys.stderr)
    
    @staticmethod
    def _create_log_directory(directory: str) -> bool:
        """
        Create the log directory if it doesn't exist.
        
        Args:
            directory: Path to the log directory
            
        Returns:
            True if directory exists or was created successfully, False otherwise
        """
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except PermissionError:
            print(f"Error: Permission denied creating log directory: {directory}", file=sys.stderr)
            return False
        except OSError as e:
            print(f"Error: Could not create log directory {directory}: {e}", file=sys.stderr)
            return False
    
    @staticmethod
    def _create_file_handler(
        log_file: str,
        level: int,
        formatter: logging.Formatter,
        max_bytes: int,
        backup_count: int
    ) -> Optional[RotatingFileHandler]:
        """
        Create a rotating file handler with error handling.
        
        Args:
            log_file: Path to the log file
            level: Logging level for this handler
            formatter: Formatter to use for log messages
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            
        Returns:
            RotatingFileHandler instance or None if creation failed
        """
        try:
            handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            handler.setLevel(level)
            handler.setFormatter(formatter)
            return handler
        except (OSError, PermissionError) as e:
            print(f"Error: Could not create file handler for {log_file}: {e}", file=sys.stderr)
            return None
    
    @staticmethod
    def setup_logging(config: Optional[LoggerConfig] = None) -> None:
        """
        Configure logging for the application with rotating file handlers.
        
        This method is thread-safe and will only initialize logging once.
        
        Args:
            config: Optional LoggerConfig instance. If None, uses default configuration.
        
        Features:
        - Ensures the log directory exists and optionally clears old logs
        - Sets up a standard log file (configurable level)
        - Sets up a detailed debug log file
        - Both file handlers rotate based on configuration
        - Configures a console logger with optional message filtering
        """
        # Thread-safe initialization check
        with Logger._lock:
            if Logger._logger_configured:
                return
            Logger._logger_configured = True
            
            # Store configuration
            Logger._config = config or LoggerConfig()
            cfg = Logger._config
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.DEBUG)
        
        # Create log directory
        if not Logger._create_log_directory(cfg.log_directory):
            print("Fatal: Could not create log directory. Logging may not work properly.", file=sys.stderr)
            return
        
        # Clear existing logs if configured
        if cfg.clear_on_startup:
            log_files = [
                os.path.join(cfg.log_directory, 'violetwing.log'),
                os.path.join(cfg.log_directory, 'violetwing_detailed.log')
            ]
            Logger._clear_existing_logs(log_files, cfg.backup_count)
        
        # Create formatters
        standard_formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(levelname)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        detailed_formatter = logging.Formatter(
            fmt='[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(threadName)s] [%(name)s:%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Create file handlers
        standard_log = os.path.join(cfg.log_directory, 'violetwing.log')
        file_handler = Logger._create_file_handler(
            standard_log,
            cfg.file_level,
            standard_formatter,
            cfg.max_bytes,
            cfg.backup_count
        )
        if file_handler:
            root_logger.addHandler(file_handler)
        
        detailed_log = os.path.join(cfg.log_directory, 'violetwing_detailed.log')
        detailed_handler = Logger._create_file_handler(
            detailed_log,
            cfg.detailed_level,
            detailed_formatter,
            cfg.max_bytes,
            cfg.backup_count
        )
        if detailed_handler:
            root_logger.addHandler(detailed_handler)
        
        # Create console handler with filters
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(cfg.console_level)
        stream_handler.setFormatter(standard_formatter)
        
        # Add suppress filter if patterns are configured
        if cfg.suppress_patterns:
            suppress_filter = SuppressErrorFilter(cfg.suppress_patterns)
            stream_handler.addFilter(suppress_filter)
        
        root_logger.addHandler(stream_handler)
        
        # Log initialization success
        logger = Logger.get_logger()
        logger.info("Logging system initialized successfully.")
        logger.debug(f"Standard log file: {standard_log}")
        logger.debug(f"Detailed log file: {detailed_log}")
    
    @staticmethod
    def get_logger(name: Optional[str] = None) -> logging.Logger:
        """
        Get a logger instance (thread-safe).
        
        Args:
            name: Optional logger name. If provided, returns a named logger.
                  If None, returns the cached module logger.
        
        Returns:
            Logger instance
        """
        if name:
            return logging.getLogger(name)
        
        # Thread-safe singleton pattern for default logger
        if Logger._logger is None:
            with Logger._lock:
                if Logger._logger is None:
                    Logger._logger = logging.getLogger(__name__)
        
        return Logger._logger
    
    @staticmethod
    def shutdown() -> None:
        """Properly shut down the logging system."""
        logger = Logger.get_logger()
        logger.info("Logging system shutting down.")
        logging.shutdown()
    
    @staticmethod
    def clear_logs() -> None:
        """Manually clear all log files and their backups."""
        cfg = Logger._config or LoggerConfig()
        log_files = [
            os.path.join(cfg.log_directory, 'violetwing.log'),
            os.path.join(cfg.log_directory, 'violetwing_detailed.log')
        ]
        Logger._clear_existing_logs(log_files, cfg.backup_count)
        logger = Logger.get_logger()
        logger.info("Log files cleared manually.")
