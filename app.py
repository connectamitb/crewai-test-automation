import os
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from routes.test_cases import test_cases_bp

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key")

# Register blueprints
app.register_blueprint(test_cases_bp, url_prefix='/api')

@app.route('/')
def index():
    """Render the dashboard homepage"""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)