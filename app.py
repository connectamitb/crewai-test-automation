"""Main application entry point."""
import os
import sys
import logging
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
import traceback

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

# Create Flask app
logger.info("Creating Flask application")
app = Flask(__name__)

# Set a default development secret key if none provided
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_key_123")
logger.info("Flask app instance created")

# Blueprint registration will be attempted but not required for basic functionality
try:
    logger.info("Checking for test_cases blueprint")
    from routes import test_cases_bp
    app.register_blueprint(test_cases_bp, url_prefix='/api/v1')
    logger.info("Successfully registered test_cases blueprint")
except ImportError:
    logger.warning("test_cases blueprint not found - continuing with basic functionality")
except Exception as e:
    logger.error(f"Error registering blueprint: {str(e)}")
    logger.debug(traceback.format_exc())

@app.route('/')
def index():
    """Render the dashboard homepage"""
    try:
        logger.info("Rendering index page")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index: {str(e)}")
        return jsonify({"error": "Failed to render dashboard"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

# We need this for gunicorn
application = app

if __name__ == '__main__':
    try:
        logger.info("Starting Flask development server")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {str(e)}")
        logger.error(f"Startup error details: {traceback.format_exc()}")
        sys.exit(1)