"""Main application entry point."""
import os
import logging
from flask import Flask, render_template
from dotenv import load_dotenv
from routes.test_cases import test_cases_bp, init_integrations

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure the Flask application"""
    try:
        # Create Flask app
        app = Flask(__name__)
        app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key")

        # Initialize integrations before registering blueprints
        init_integrations()

        # Register blueprints
        app.register_blueprint(test_cases_bp, url_prefix='/api/v1')

        @app.route('/')
        def index():
            """Render the dashboard homepage"""
            return render_template('index.html')

        @app.errorhandler(404)
        def not_found(error):
            return {"error": "Not found"}, 404

        @app.errorhandler(500)
        def server_error(error):
            return {"error": "Internal server error"}, 500

        return app

    except Exception as e:
        logger.error(f"Failed to initialize Flask app: {str(e)}")
        raise

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)