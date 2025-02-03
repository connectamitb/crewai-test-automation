import logging
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from services.code_analysis import CursorAIService

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
cursor_ai = CursorAIService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_requirement', methods=['POST'])
def submit_requirement():
    requirement = request.form.get('requirement')
    if not requirement:
        return jsonify({'error': 'Test requirement is required'}), 400

    # Here you would typically process the requirement
    # For now, we'll just log it
    logging.debug(f"Received test requirement: {requirement}")

    return jsonify({'message': 'Test requirement received successfully'})

@app.route('/analyze-code', methods=['POST'])
def analyze_code():
    """Endpoint to analyze code using Cursor AI"""
    try:
        code = request.json.get('code')
        if not code:
            return jsonify({'error': 'Code is required'}), 400

        analysis_result = cursor_ai.analyze_code(code)
        return jsonify(analysis_result)
    except Exception as e:
        logging.error(f"Error in code analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/auth', methods=['POST'])
def auth():
    try:
        auth_data = request.get_json()
        # For now, just log the token receipt and return success
        logging.info("Received authentication token")
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)