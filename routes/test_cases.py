"""Routes for test case management"""
import logging
from flask import Blueprint, request, jsonify
from testai.agents.test_case_mapping import TestCaseMappingAgent

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
test_cases_bp = Blueprint('test_cases', __name__)

# Initialize agents with error handling
test_case_mapping_agent = None
try:
    test_case_mapping_agent = TestCaseMappingAgent()
    logger.info("TestCaseMappingAgent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize TestCaseMappingAgent: {str(e)}")
    # Continue without the agent - core app functionality remains available

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

        if not test_case_mapping_agent:
            logger.error("Test case mapping agent not available")
            return jsonify({
                "error": "Service temporarily unavailable",
                "message": "Test case generation service is initializing or offline"
            }), 503

        requirement_text = data['requirement']
        logger.info(f"Processing requirement: {requirement_text}")

        result = test_case_mapping_agent.execute_task({
            'requirement': {
                'description': requirement_text,
                'project_key': data.get('project_key')
            }
        })

        response = {
            "status": "success",
            "test_case": result['test_case'],
            "storage_status": result.get('storage', {})
        }

        return jsonify(response), 201

    except Exception as e:
        logger.error(f"Error in generate_test_case: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@test_cases_bp.route('/test-cases/search', methods=['GET'])
def search_test_cases():
    """Search for test cases using vector similarity search"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({"error": "Search query is required"}), 400

        logger.info(f"Received search request with query: {query}")

        if not test_case_mapping_agent:
            logger.error("Test case mapping agent not available")
            return jsonify({
                "status": "error",
                "message": "Search service temporarily unavailable",
                "results": []
            }), 200  # Return empty results instead of error

        results = test_case_mapping_agent.query_test_cases(query)
        logger.info(f"Found {len(results)} test cases")

        return jsonify({
            "status": "success",
            "results": results,
            "total": len(results)
        }), 200

    except Exception as e:
        logger.error(f"Error searching test cases: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e),
            "results": []
        }), 200  # Return empty results with error message

@test_cases_bp.route('/test-cases/<name>', methods=['GET'])
def get_test_case(name):
    """Get a test case by name"""
    try:
        if not test_case_mapping_agent or not test_case_mapping_agent.weaviate_client:
            logger.error("Test case service not available")
            return jsonify({
                "error": "Service temporarily unavailable"
            }), 503

        result = test_case_mapping_agent.weaviate_client.get_test_case(name)
        if result is None:
            return jsonify({"error": "Test case not found"}), 404

        return jsonify({"status": "success", "test_case": result}), 200

    except Exception as e:
        logger.error(f"Error retrieving test case: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500