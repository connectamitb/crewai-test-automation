import os
import logging
from flask import Flask, render_template, request, jsonify
from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv
from testai.agents.requirement_input import RequirementInputAgent
from testai.agents.test_case_mapping import TestCaseMappingAgent
from testai.agents.validation_agent import ValidationAgent
from testai.agents.storage_integration_agent import StorageIntegrationAgent
import weaviate
from weaviate.util import generate_uuid5

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key")

# Initialize Weaviate client with v4 API
try:
    weaviate_client = weaviate.WeaviateClient(
        connection_params=weaviate.connect.ConnectionParams.from_url(
            url="http://localhost:8080",
            grpc_port=50051
        )
    )

    # Create TestCase class in Weaviate if it doesn't exist
    class_obj = {
        "class": "TestCase",
        "properties": [
            {"name": "title", "dataType": ["text"]},
            {"name": "description", "dataType": ["text"]},
            {"name": "steps", "dataType": ["object"]},
            {"name": "tags", "dataType": ["text[]"]},
            {"name": "metadata", "dataType": ["object"]}
        ],
        "vectorizer": "text2vec-contextionary"
    }
    weaviate_client.schema.create_class(class_obj)
except Exception as e:
    logger.warning(f"Weaviate initialization warning: {str(e)}")

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

        if not validation_result.get("is_valid", False):
            return jsonify({
                "status": "error",
                "message": "Test case validation failed",
                "validation_errors": validation_result.get("suggestions", [])
            }), 400

        # Step 4: Store test case in Weaviate
        try:
            if 'weaviate_client' in globals():
                uuid = generate_uuid5(test_case["title"])
                properties = {
                    "title": test_case["title"],
                    "description": test_case["description"],
                    "steps": {
                        "given": test_case["format"]["given"],
                        "when": test_case["format"]["when"],
                        "then": test_case["format"]["then"]
                    },
                    "tags": test_case["format"]["tags"],
                    "metadata": test_case["metadata"]
                }
                weaviate_client.data.create(
                    uuid=uuid,
                    class_name="TestCase",
                    properties=properties
                )
                logger.info(f"Test case stored in Weaviate with UUID: {uuid}")
        except Exception as e:
            logger.error(f"Error storing in Weaviate: {str(e)}")

        # Return the complete test case structure
        return jsonify({
            "status": "success",
            "test_case": test_case
        })

    except Exception as e:
        logger.error(f"Error creating test case: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)