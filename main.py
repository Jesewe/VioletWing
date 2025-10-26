import sys
import signal
from pathlib import Path

from classes.logger import Logger
from classes.config_manager import ConfigManager

from gui.main_window import MainWindow

def setup_signal_handlers(logger):
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main application entry point."""    
    # Set up logging for the application.
    try:
        Logger.setup_logging()
        logger = Logger.get_logger("main")
    except Exception as e:
        print(f"Failed to setup logging: {e}", file=sys.stderr)
        sys.exit(1)

    # Set up signal handlers for graceful shutdown
    setup_signal_handlers(logger)

    # Log the loaded version.
    try:
        version = ConfigManager.VERSION
        logger.info("Loaded version: %s", version)
    except Exception as e:
        logger.warning("Could not load version information: %s", e)

    # Log application startup
    logger.info("Starting application...")

    exit_code = 0
    window = None

    try:
        # Create and run the main application window.
        window = MainWindow()
        logger.debug("Main window created successfully")
        window.run()
        logger.debug("Application completed normally")
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        exit_code = 0  # Clean exit on Ctrl+C
    except ImportError as e:
        logger.exception("Failed to import required modules. Please ensure all dependencies are installed.")
        exit_code = 2
    except Exception as e:
        logger.exception("An unexpected error occurred in the main application loop.")
        exit_code = 1
    finally:
        # Ensure proper cleanup
        if window and hasattr(window, 'cleanup'):
            try:
                logger.debug("Cleaning up window resources...")
                window.cleanup()
            except Exception as cleanup_error:
                logger.warning("Error during cleanup: %s", cleanup_error)
        
        logger.debug("Application shutting down")
        
        # Ensure logging is properly flushed
        try:
            Logger.shutdown()
        except Exception:
            pass  # Don't let logging errors prevent shutdown

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
