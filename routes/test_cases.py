"""Routes for test case management"""
import logging
from flask import Blueprint, request, jsonify, current_app
from integrations.models import TestCase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
test_cases_bp = Blueprint('test_cases', __name__)

@test_cases_bp.route('/api/v1/test-cases', methods=['POST'])
def create_test_case():
    """Create and store a test case"""
    try:
        logger.info("Received request to create test case")
        logger.debug(f"Request data: {request.get_json() if request.is_json else 'No JSON data'}")

        if not request.is_json:
            logger.error("Request content type is not application/json")
            return jsonify({"error": "Content type must be application/json"}), 400

        data = request.get_json()
        logger.debug(f"Received data: {data}")

        if not data:
            logger.error("No data received in request")
            return jsonify({"error": "No data provided"}), 400

        if 'requirement' not in data:
            logger.error("Missing requirement in request data")
            return jsonify({"error": "Requirement text is required"}), 400

        # Format the test case data with required structure
        formatted_test_case = {
            "title": data.get('title', 'Test Case from Requirement'),
            "description": data['requirement'],
            "precondition": "System is accessible and ready for testing",
            "steps": [],
            "format": {
                "given": ["System is accessible", "Test environment is ready"],
                "when": ["User performs the required actions"],
                "then": ["Expected outcomes are verified"]
            },
            "metadata": {
                "priority": data.get('priority', 'Normal'),
                "automation_needed": data.get('automation_needed', 'TBD'),
                "tags": data.get('tags', [])
            }
        }

        # Create test case instance
        test_case = TestCase(
            name=formatted_test_case['title'],
            objective=formatted_test_case['description'],
            precondition=formatted_test_case['precondition'],
            automation_needed=formatted_test_case['metadata']['automation_needed'],
            steps=formatted_test_case['steps'],
            tags=formatted_test_case['metadata']['tags'],
            priority=formatted_test_case['metadata']['priority']
        )

        # Get Weaviate client from app context
        weaviate_client = current_app.config.get('weaviate_client')

        # Store in Weaviate if available
        storage_status = {"memory": True, "weaviate": False}
        if weaviate_client and weaviate_client.is_healthy():
            test_case_id = weaviate_client.store_test_case(test_case)
            storage_status["weaviate"] = bool(test_case_id)
            logger.info(f"Test case stored in Weaviate with ID: {test_case_id}")
        else:
            logger.warning("Weaviate storage skipped - client unavailable")

        # Return the formatted test case in the response
        response_data = {
            "status": "success",
            "test_case": formatted_test_case,
            "storage_status": storage_status
        }

        logger.debug(f"Sending response: {response_data}")
        return jsonify(response_data), 201

    except Exception as e:
        logger.error(f"Error creating test case: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@test_cases_bp.route('/api/v1/test-cases/search', methods=['GET'])
def search_test_cases():
    """Search for test cases using vector similarity search"""
    try:
        query = request.args.get('q', '')
        if not query:
            logger.warning("Empty search query received")
            return jsonify({
                "status": "success",
                "message": "Please provide a search query",
                "results": []
            }), 200

        logger.info(f"Searching test cases with query: {query}")

        # Get Weaviate client from app context
        weaviate_client = current_app.config.get('weaviate_client')

        if not weaviate_client or not weaviate_client.is_healthy():
            logger.warning("Weaviate client not available for search")
            return jsonify({
                "status": "error",
                "message": "Search service temporarily unavailable",
                "results": []
            }), 503

        results = weaviate_client.search_test_cases(query)
        logger.info(f"Found {len(results)} test cases")

        # Transform results if needed to match frontend expectations
        formatted_results = []
        for result in results:
            formatted_result = {
                "name": result.get("title", "Untitled"),
                "description": result.get("description", ""),
                "format": result.get("format", {
                    "given": [],
                    "when": [],
                    "then": []
                }),
                "metadata": result.get("metadata", {})
            }
            formatted_results.append(formatted_result)

        return jsonify({
            "status": "success",
            "results": formatted_results,
            "total": len(formatted_results)
        }), 200

    except Exception as e:
        logger.error(f"Error searching test cases: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e),
            "results": []
        }), 500

@test_cases_bp.route('/api/v1/test-cases/<name>', methods=['GET'])
def get_test_case(name):
    """Get a test case by name"""
    try:
        # Get Weaviate client from app context
        weaviate_client = current_app.config.get('weaviate_client')

        if not weaviate_client or not weaviate_client.is_healthy():
            logger.error("Weaviate client not available")
            return jsonify({
                "error": "Service temporarily unavailable"
            }), 503

        result = weaviate_client.get_test_case(name)
        if result is None:
            return jsonify({"error": "Test case not found"}), 404

        return jsonify({"status": "success", "test_case": result}), 200

    except Exception as e:
        logger.error(f"Error retrieving test case: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500