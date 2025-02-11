import os
import logging
from flask import Flask, render_template, request, jsonify
from crewai import Agent, Task, Crew, Process
from testai.agents.manual_test_agent import ManualTestAgent, TestCase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key")

# Initialize CrewAI agents
requirement_input_agent = Agent(
    name="RequirementInput",
    role="Requirements Processor",
    goal="Process and validate test requirements",
    backstory="Expert in analyzing and validating test requirements",
    verbose=True
)

analyzer_agent = Agent(
    name="Analyzer",
    role="Test Analyzer",
    goal="Analyze test requirements and generate test specifications",
    backstory="Expert in test analysis and requirement decomposition",
    verbose=True
)

test_case_mapping_agent = Agent(
    name="TestCaseMapper",
    role="Test Case Designer",
    goal="Generate comprehensive test cases from requirements",
    backstory="Expert in test case design and automation",
    verbose=True
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_requirement', methods=['POST'])
def submit_requirement():
    """Submit a new test requirement for processing"""
    try:
        requirement = request.form.get('requirement')
        if not requirement:
            return jsonify({'error': 'Test requirement is required'}), 400

        # Create CrewAI crew for processing the requirement
        crew = Crew(
            agents=[requirement_input_agent, analyzer_agent, test_case_mapping_agent],
            process=Process.sequential
        )

        # Define tasks for the crew
        tasks = [
            Task(
                description=f"Analyze and validate the following test requirement: {requirement}",
                agent=requirement_input_agent
            ),
            Task(
                description="Generate test specifications from the validated requirement",
                agent=analyzer_agent
            ),
            Task(
                description="Create detailed test cases based on the specifications",
                agent=test_case_mapping_agent
            )
        ]

        # Execute the crew tasks
        result = crew.kickoff()
        logger.info(f"CrewAI processing completed for requirement: {requirement}")

        return jsonify({
            'message': 'Test requirement processed successfully',
            'result': result
        })

    except Exception as e:
        logger.error(f"Error processing requirement: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-code', methods=['POST'])
def analyze_code():
    """Endpoint to analyze code using CrewAI"""
    try:
        code = request.json.get('code')
        if not code:
            return jsonify({'error': 'Code is required'}), 400

        # Create an analysis task with the analyzer agent
        analysis_task = Task(
            description=f"Analyze the following code for test cases: {code}",
            agent=analyzer_agent
        )

        crew = Crew(
            agents=[analyzer_agent],
            tasks=[analysis_task],
            process=Process.sequential
        )

        analysis_result = crew.kickoff()
        return jsonify({'analysis': analysis_result})

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
    """Create a test case using the TestCaseMapping agent"""
    try:
        data = request.json
        requirement = data.get('requirement')
        if not requirement:
            return jsonify({"error": "No requirement provided"}), 400

        task = Task(
            description=f"Create test cases for requirement: {requirement}",
            agent=test_case_mapping_agent
        )

        crew = Crew(
            agents=[test_case_mapping_agent],
            tasks=[task],
            process=Process.sequential
        )

        result = crew.kickoff()
        logger.info(f"Generated test case for requirement: {requirement[:100]}...")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error creating test case: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)