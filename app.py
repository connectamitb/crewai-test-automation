import os
import logging
from flask import Flask, render_template, request, jsonify
from testai.agents.manual_test_agent import ManualTestAgent, TestCase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_requirement', methods=['POST'])
def submit_requirement():
    requirement = request.form.get('requirement')
    if not requirement:
        return jsonify({'error': 'Test requirement is required'}), 400

    # Here you would typically process the requirement
    logger.debug(f"Received test requirement: {requirement}")
    return jsonify({'message': 'Test requirement received successfully'})

@app.route('/analyze-code', methods=['POST'])
def analyze_code():
    """Endpoint to analyze code using Cursor AI"""
    try:
        code = request.json.get('code')
        if not code:
            return jsonify({'error': 'Code is required'}), 400

        #analysis_result = cursor_ai.analyze_code(code) #Removed because cursor_ai is not defined in edited code
        #Returning a placeholder for now. Replace with actual analysis logic if needed.
        return jsonify({'analysis': 'Analysis result placeholder'}) 
    except Exception as e:
        logger.error(f"Error in code analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/auth', methods=['POST'])
def auth():
    try:
        auth_data = request.get_json()
        # For now, just log the token receipt and return success
        logger.info("Received authentication token")
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/test-cases', methods=['POST'])
def create_test_case():
    """Create a test case using the ManualTestAgent"""
    try:
        data = request.json
        requirement = data.get('requirement')
        if not requirement:
            return jsonify({"error": "No requirement provided"}), 400

        # Create an instance of ManualTestAgent
        agent = ManualTestAgent()

        # Prepare the task for the agent
        task = {
            'requirement': requirement,
            'timestamp': data.get('timestamp')
        }

        # Execute the task and get the result
        result = agent.execute_task(task)

        logger.info(f"Generated test case for requirement: {requirement[:100]}...")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error creating test case: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)