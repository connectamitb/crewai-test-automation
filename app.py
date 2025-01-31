import logging
from flask import Flask, render_template, request, jsonify

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

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
