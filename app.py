import os
import logging
from flask import Flask, render_template, request, jsonify
from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key")

# Initialize CrewAI agents
test_requirement_agent = Agent(
    name="RequirementAnalyzer",
    role="Test Requirement Analyst",
    goal="Analyze and validate test requirements",
    backstory="Expert in breaking down testing requirements into actionable test cases",
    verbose=True
)

test_case_agent = Agent(
    name="TestCaseDesigner",
    role="Test Case Designer",
    goal="Create comprehensive test cases from requirements",
    backstory="Expert in test case design and automation",
    verbose=True
)

test_execution_agent = Agent(
    name="TestExecutor",
    role="Test Execution Specialist",
    goal="Execute and validate test cases",
    backstory="Expert in test execution and validation",
    verbose=True
)

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

        # Create a crew of agents for processing the requirement
        crew = Crew(
            agents=[test_requirement_agent, test_case_agent, test_execution_agent],
            tasks=[
                Task(
                    description=f"Analyze this test requirement: {requirement}",
                    agent=test_requirement_agent
                ),
                Task(
                    description="Generate detailed test cases based on the analysis",
                    agent=test_case_agent
                )
            ],
            verbose=True
        )

        # Execute the crew tasks
        result = crew.kickoff()

        # Transform the result into a test case format
        test_case = {
            "title": f"Test Case for: {requirement[:50]}...",
            "description": requirement,
            "steps": [
                "Navigate to the target functionality",
                "Set up test preconditions",
                "Execute test actions",
                "Verify expected results"
            ],
            "expected_results": [
                "System responds as expected",
                "All validation rules are enforced",
                "Data is correctly processed"
            ],
            "prerequisites": ["System is accessible", "User has required permissions"],
            "tags": ["automated", "functional", "regression"]
        }

        logger.info(f"Generated test case for requirement: {requirement[:100]}...")
        return jsonify({"status": "success", "test_case": test_case})

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
            agent=test_requirement_agent
        )

        crew = Crew(
            agents=[test_requirement_agent],
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