import os
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from testai.agents.test_case_mapping import TestCaseMappingAgent
from testai.agents.validation_agent import ValidationAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key")

# Initialize agents
test_case_mapping_agent = TestCaseMappingAgent()
validation_agent = ValidationAgent()

@app.route('/')
def index():
    """Render the dashboard homepage"""
    return render_template('index.html')

@app.route('/api/test-cases', methods=['POST'])
def create_test_case():
    """Create test cases from requirements using CrewAI agents"""
    try:
        data = request.json
        requirement = data.get('requirement')
        if not requirement:
            return jsonify({"status": "error", "message": "No requirement provided"}), 400

        # Generate test case using TestCaseMappingAgent
        test_case_result = test_case_mapping_agent.execute_task({
            "requirement": requirement,
            "timestamp": "2025-02-11"
        })

        if not test_case_result or "test_case" not in test_case_result:
            return jsonify({
                "status": "error",
                "message": "Failed to generate test case"
            }), 500

        test_case = test_case_result["test_case"]

        # Validate the generated test case
        validation_result = validation_agent.execute_task({
            "test_case": test_case
        })

        if not validation_result.get("is_valid", False):
            return jsonify({
                "status": "error",
                "message": "Test case validation failed",
                "validation_errors": validation_result.get("suggestions", [])
            }), 400

        # Return the complete test case structure
        return jsonify({
            "status": "success",
            "test_case": test_case
        })

    except Exception as e:
        logger.error(f"Error creating test case: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)