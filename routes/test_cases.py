"""Routes for test case management"""
import logging
from flask import Blueprint, request, jsonify
from testai.agents.test_case_mapping import TestCaseMappingAgent
from integrations.weaviate_integration import WeaviateIntegration
from integrations.zephyr_integration import ZephyrIntegration

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
test_cases_bp = Blueprint('test_cases', __name__)

# Initialize agents
test_case_mapping_agent = TestCaseMappingAgent()

@test_cases_bp.route('/test-cases', methods=['POST'])
def generate_test_case():
    """Generate and store test cases from requirements"""
    try:
        logger.info("Received request to generate test case")

        if not request.is_json:
            logger.error("Request content type is not application/json")
            return jsonify({"error": "Content type must be application/json"}), 400

        data = request.get_json()
        logger.debug(f"Received data: {data}")

        if not data or 'requirement' not in data:
            logger.error("Missing requirement in request data")
            return jsonify({"error": "Requirement text is required"}), 400

        requirement_text = data['requirement']
        logger.info(f"Processing requirement: {requirement_text}")

        # Generate test case using the mapping agent
        try:
            test_case = test_case_mapping_agent.execute_task({
                'requirement': {
                    'description': requirement_text,
                    'project_key': data.get('project_key')
                }
            })
            logger.debug(f"Test case mapping result: {test_case}")

            if not test_case or 'test_case' not in test_case:
                logger.error(f"Test case mapping failed: {test_case}")
                return jsonify({"error": "Failed to generate test case"}), 500

            # Format response
            response = {
                "status": "success",
                "test_case": test_case['test_case'],
                "storage_status": test_case.get('storage', {})
            }

            return jsonify(response), 201

        except Exception as e:
            logger.error(f"Error in test case generation: {str(e)}", exc_info=True)
            return jsonify({"error": f"Test case generation error: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"General error in generate_test_case: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@test_cases_bp.route('/test-cases/search', methods=['GET'])
def search_test_cases():
    """Search for test cases using vector similarity search"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({"error": "Search query is required"}), 400

        logger.info(f"Received search request with query: {query}")

        # Initialize Weaviate client if not already initialized
        weaviate_client = WeaviateIntegration()

        # Search using the test case mapping agent which handles both vector and memory search
        logger.info("Executing search using test case mapping agent...")
        results = test_case_mapping_agent.query_test_cases(query)

        logger.info(f"Found {len(results)} test cases matching query: {query}")
        logger.debug(f"Search results: {results}")

        return jsonify({
            "status": "success",
            "results": results,
            "total": len(results)
        }), 200

    except Exception as e:
        logger.error(f"Error searching test cases: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@test_cases_bp.route('/test-cases/<name>', methods=['GET'])
def get_test_case(name):
    """Get a test case by name"""
    try:
        weaviate_client = WeaviateIntegration()
        result = weaviate_client.get_test_case(name)

        if result is None:
            return jsonify({"error": "Test case not found"}), 404

        return jsonify({"status": "success", "test_case": result}), 200

    except Exception as e:
        logger.error(f"Error retrieving test case: {str(e)}")
        return jsonify({"error": str(e)}), 500