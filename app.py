"""Main application entry point."""
import os
import sys
import logging
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import traceback
from integrations.weaviate_integration import WeaviateIntegration
from integrations.weaviate_schema import WeaviateSchema
from routes.health import health_bp
from routes.test_cases import test_cases_bp

# Configure logging
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
app = Flask(__name__)
CORS(app)

# Initialize Weaviate client
try:
    weaviate_client = WeaviateIntegration()
    app.config['weaviate_client'] = weaviate_client
    logger.info("Weaviate client initialized")
except Exception as e:
    logger.error(f"Failed to initialize Weaviate client: {str(e)}")
    app.config['weaviate_client'] = None

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(test_cases_bp)

@app.before_request
def log_request_info():
    """Log details about each request"""
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())

@app.route('/')
def index():
    """Render the main page"""
    try:
        logger.debug("Rendering index page")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/test-cases')
def test_cases_page():
    """Render test cases management page"""
    try:
        logger.debug("Rendering test cases page")
        return render_template('test_cases.html')
    except Exception as e:
        logger.error(f"Error rendering test cases page: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {str(error)}")
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    try:
        # Get port from environment variable with default to 5000
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting Flask server on port {port}")

        app.run(
            host='0.0.0.0',
            port=port,
            debug=True
        )
    except Exception as e:
        logger.error(f"Failed to start app: {str(e)}")
        sys.exit(1)