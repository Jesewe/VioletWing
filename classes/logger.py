import os
import logging
from logging.handlers import RotatingFileHandler
import sys

class SuppressErrorFilter(logging.Filter):
    """A logging filter to suppress messages containing a specific pattern."""
    def __init__(self, pattern):
        super().__init__()
        self.pattern = pattern

    def filter(self, record):
        """Return False if the pattern is found in the message, True otherwise."""
        return self.pattern not in record.getMessage()

class Logger:
    """
    A class to handle logging for the application.
    It sets up rotating log files and console logging with detailed context.
    """
    LOG_DIRECTORY = os.path.expanduser(r'~\AppData\Local\VioletWing\logs')
    LOG_FILE = os.path.join(LOG_DIRECTORY, 'violetwing.log')
    DETAILED_LOG_FILE = os.path.join(LOG_DIRECTORY, 'violetwing_detailed.log')
    
    _logger = None
    _logger_configured = False

    @staticmethod
    def _clear_existing_logs():
        """Clears existing log files and their backups."""
        log_files = [Logger.LOG_FILE, Logger.DETAILED_LOG_FILE]
        for log_file in log_files:
            try:
                if os.path.exists(log_file):
                    # Clear the main log file
                    with open(log_file, 'w') as f:
                        f.truncate(0)
                    
                    # Remove backup files
                    for i in range(1, 6):
                        backup_file = f"{log_file}.{i}"
                        if os.path.exists(backup_file):
                            os.remove(backup_file)
            except Exception as e:
                print(f"Warning: Could not clear log file {log_file}: {e}", file=sys.stderr)

    @staticmethod
    def setup_logging():
        """
        Configures logging for the application with rotating file handlers.
        - Ensures the log directory exists and clears old logs.
        - Sets up a standard log file (INFO level) and a detailed log file (DEBUG level).
        - Both file handlers rotate, keeping 5 backups of 5MB each.
        - Configures a console logger (INFO level).
        """
        if Logger._logger_configured:
            return
        Logger._logger_configured = True
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.DEBUG)

        try:
            os.makedirs(Logger.LOG_DIRECTORY, exist_ok=True)
            Logger._clear_existing_logs()
        except Exception as e:
            print(f"Fatal: Error creating log directory or clearing logs in {Logger.LOG_DIRECTORY}: {e}", file=sys.stderr)
            return

        # Standard formatter for the main log file and console
        standard_formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(levelname)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Detailed formatter for the debug log file
        detailed_formatter = logging.Formatter(
            fmt='[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(threadName)s] [%(name)s:%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        try:
            # Rotating file handler for the standard log
            file_handler = RotatingFileHandler(
                Logger.LOG_FILE, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(standard_formatter)
            root_logger.addHandler(file_handler)

            # Rotating file handler for the detailed debug log
            detailed_handler = RotatingFileHandler(
                Logger.DETAILED_LOG_FILE, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
            )
            detailed_handler.setLevel(logging.DEBUG)
            detailed_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(detailed_handler)
        except Exception as e:
            print(f"Fatal: Error setting up file handlers: {e}", file=sys.stderr)

        # Console stream handler
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(standard_formatter)
        # Suppress noisy, non-critical errors from the console
        suppress_filter = SuppressErrorFilter("Error drawing entity: 'NoneType' object is not subscriptable")
        stream_handler.addFilter(suppress_filter)
        root_logger.addHandler(stream_handler)

        logger = Logger.get_logger()
        logger.info("Logging system initialized successfully.")
        logger.debug(f"Standard log file: {Logger.LOG_FILE}")
        logger.debug(f"Detailed log file: {Logger.DETAILED_LOG_FILE}")

    @staticmethod
    def get_logger(name=None):
        """
        Returns a logger instance. If a name is provided, it returns a logger
        with that name; otherwise, it returns the root logger for the module.
        """
        if name:
            return logging.getLogger(name)
        if Logger._logger is None:
            Logger._logger = logging.getLogger(__name__)
        return Logger._logger

    @staticmethod
    def shutdown():
        """Properly shuts down the logging system."""
        logger = Logger.get_logger()
        logger.info("Logging system shutting down.")
        logging.shutdown()
