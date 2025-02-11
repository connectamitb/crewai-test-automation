import os
import logging
from flask import Flask, render_template, request, jsonify
from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv
from testai.agents.requirement_input import RequirementInputAgent
from testai.agents.test_case_mapping import TestCaseMappingAgent
from testai.agents.validation_agent import ValidationAgent
from testai.agents.storage_integration_agent import StorageIntegrationAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key")

# Initialize CrewAI agents
requirement_input_agent = RequirementInputAgent()
test_case_mapping_agent = TestCaseMappingAgent()
validation_agent = ValidationAgent()
storage_agent = StorageIntegrationAgent()

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
            return jsonify({"error": "No requirement provided"}), 400

        # Step 1: Process requirement using RequirementInputAgent
        processed_req = requirement  # For now, pass through the requirement directly

        # Step 2: Generate test case using TestCaseMappingAgent
        test_case_result = test_case_mapping_agent.execute_task({
            "requirement": processed_req,
            "timestamp": "2025-02-11"
        })

        if not test_case_result or "test_case" not in test_case_result:
            return jsonify({
                "status": "error",
                "message": "Failed to generate test case"
            }), 500

        test_case = test_case_result["test_case"]

        # Step 3: Validate the generated test case
        validation_result = validation_agent.execute_task({
            "test_case": test_case
        })

        if validation_result.get("is_valid", False):
            # Step 4: Store test case
            storage_result = storage_agent.execute_task({
                "test_case": test_case
            })

            return jsonify({
                "status": "success",
                "test_case": {
                    "title": test_case.get("title", ""),
                    "description": test_case.get("description", ""),
                    "prerequisites": test_case.get("format", {}).get("given", []),
                    "steps": test_case.get("format", {}).get("when", []),
                    "expected_results": test_case.get("format", {}).get("then", []),
                    "tags": test_case.get("format", {}).get("tags", []),
                    "storage_info": storage_result
                }
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Test case validation failed",
                "validation_errors": validation_result.get("warnings", [])
            }), 400

    except Exception as e:
        logger.error(f"Error creating test case: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-code', methods=['POST'])
def analyze_code():
    """Analyze code using CrewAI agents"""
    try:
        code = request.json.get('code')
        if not code:
            return jsonify({'error': 'Code is required'}), 400

        analysis_task = Task(
            description=f"Analyze this code for test cases: {code}",
            agent=requirement_input_agent
        )

        crew = Crew(
            agents=[requirement_input_agent],
            tasks=[analysis_task],
            process=Process.sequential
        )

        analysis_result = crew.kickoff()
        return jsonify({'status': 'success', 'analysis': analysis_result})

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)