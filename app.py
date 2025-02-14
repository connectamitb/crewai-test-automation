"""Main application entry point."""
import os
import sys
import logging
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import traceback
from integrations.weaviate_integration import WeaviateIntegration

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
CORS(app)  # Enable CORS for all routes
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_key_123")

# Configure for Replit environment
app.config['PREFERRED_URL_SCHEME'] = 'https'

def init_weaviate():
    """Initialize Weaviate client"""
    try:
        logger.info("Attempting to initialize Weaviate client...")
        # Log Weaviate configuration (without sensitive values)
        weaviate_url = os.getenv("WEAVIATE_URL")
        weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

        if not weaviate_url or not weaviate_api_key:
            logger.error("Missing Weaviate credentials")
            logger.debug(f"WEAVIATE_URL present: {bool(weaviate_url)}")
            logger.debug(f"WEAVIATE_API_KEY present: {bool(weaviate_api_key)}")
            return False

        logger.info(f"Initializing Weaviate with URL: {weaviate_url}")
        weaviate_client = WeaviateIntegration()

        if weaviate_client and weaviate_client.is_healthy():
            logger.info("✅ Weaviate client initialized successfully")
            app.config['weaviate_client'] = weaviate_client
            return True
        else:
            logger.error("⚠️ Weaviate client not healthy")
            return False

    except Exception as e:
        logger.error("❌ Error initializing Weaviate client: %s", str(e))
        logger.error(traceback.format_exc())
        return False

# Initialize Weaviate client on startup
if not init_weaviate():
    logger.error("Failed to initialize Weaviate client on startup")

# Register blueprints
try:
    logger.info("Registering test_cases blueprint")
    from routes.test_cases import test_cases_bp
    app.register_blueprint(test_cases_bp)
    logger.info("Successfully registered test_cases blueprint")
except Exception as e:
    logger.error(f"Error registering blueprint: {str(e)}")
    logger.error(traceback.format_exc())

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

@app.route('/api/health')
def health_check():
    """Check system health"""
    try:
        weaviate_client = app.config.get('weaviate_client')
        weaviate_status = False
        weaviate_error = None

        if weaviate_client and weaviate_client.is_healthy():
            weaviate_status = True
        else:
            weaviate_error = "Weaviate client not healthy or not initialized"
            # Try to reinitialize
            if init_weaviate():
                weaviate_status = True
                weaviate_error = None

        status = {
            'weaviate': {
                'connected': weaviate_status,
                'error': weaviate_error
            },
            'server': True
        }

        logger.info("Health check status: %s", status)
        return jsonify(status)
    except Exception as e:
        logger.error("Health check failed: %s", str(e))
        logger.error(traceback.format_exc())
        return jsonify({
            'weaviate': {
                'connected': False,
                'error': str(e)
            },
            'server': True
        })

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {str(error)}")
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting Flask server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)