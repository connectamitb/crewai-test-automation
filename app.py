"""Main application entry point."""
import os
import sys
import logging
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import traceback

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

# Initialize Weaviate client lazily
weaviate_client = None

def init_weaviate():
    """Initialize Weaviate client if not already initialized"""
    global weaviate_client
    if weaviate_client is None:
        try:
            from integrations.weaviate_integration import WeaviateIntegration
            weaviate_client = WeaviateIntegration()

            if weaviate_client and weaviate_client.is_healthy():
                logger.info("✅ Weaviate client initialized successfully")
                app.config['weaviate_client'] = weaviate_client
                return weaviate_client
            else:
                logger.warning("⚠️ Weaviate client not healthy, running in degraded mode")
                return None

        except Exception as e:
            logger.error(f"❌ Error initializing Weaviate client: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    return weaviate_client

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
        client = init_weaviate()
        status = {
            'weaviate': client.is_healthy() if client else False,
            'server': True
        }
        logger.info(f"Health check status: {status}")
        return jsonify(status)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'weaviate': False,
            'server': True,
            'error': str(e)
        })

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {str(error)}")
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

# For gunicorn
application = app

if __name__ == '__main__':
    try:
        # Initialize Weaviate in background
        init_weaviate()

        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting Flask development server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)