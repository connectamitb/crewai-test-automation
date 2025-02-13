"""Main entry point for the Flask application."""
import sys
import logging
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    logger.info("Creating Flask application")
    app = create_app()

    if __name__ == "__main__":
        logger.info("Starting development server")
        app.run(host="0.0.0.0", port=5000, debug=True)
except Exception as e:
    logger.error(f"Failed to start application: {str(e)}", exc_info=True)
    sys.exit(1)