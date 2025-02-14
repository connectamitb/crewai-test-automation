"""Main entry point for the Flask application."""
import logging
import os
from app import app

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # Get port from environment variable
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting Flask server on port {port}")

        # Configure server for Replit
        app.run(
            host='0.0.0.0',  # Listen on all available interfaces
            port=port,
            debug=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        raise