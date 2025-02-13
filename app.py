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

def create_app():
    """Create and configure the Flask application"""
    try:
        # Create Flask app
        logger.info("Creating Flask application")
        app = Flask(__name__)
        app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key")
        logger.info("Flask app instance created")

        try:
            # Import and register blueprints
            logger.info("Attempting to register blueprints")
            from routes.test_cases import test_cases_bp
            app.register_blueprint(test_cases_bp, url_prefix='/api/v1')
            logger.info("Successfully registered all blueprints")
        except Exception as e:
            logger.error(f"Failed to register blueprints: {str(e)}")
            logger.error(f"Blueprint registration error details: {traceback.format_exc()}")

        @app.route('/')
        def index():
            """Render the dashboard homepage"""
            try:
                logger.info("Rendering index page")
                return render_template('index.html')
            except Exception as e:
                logger.error(f"Error rendering index: {str(e)}")
                logger.error(f"Template error details: {traceback.format_exc()}")
                return jsonify({"error": "Failed to render dashboard"}), 500

        @app.errorhandler(404)
        def not_found(error):
            return jsonify({"error": "Not found"}), 404

        @app.errorhandler(500)
        def server_error(error):
            logger.error(f"Server error: {str(error)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": "Internal server error"}), 500

        logger.info("Flask application creation completed successfully")
        return app

    except Exception as e:
        logger.error(f"Critical error creating Flask app: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise

if __name__ == '__main__':
    try:
        logger.info("Starting application initialization")
        app = create_app()

        if not app:
            logger.error("Application creation failed")
            sys.exit(1)

        logger.info("Starting Flask development server")
        app.run(host='0.0.0.0', port=5000, debug=True)

    except Exception as e:
        logger.error(f"Failed to start Flask server: {str(e)}")
        logger.error(f"Startup error details: {traceback.format_exc()}")
        sys.exit(1)