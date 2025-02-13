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

        # Create test case from requirement
        test_case = TestCase(
            name=data.get('title', 'Untitled Test Case'),
            objective=data['requirement'],
            precondition=data.get('precondition'),
            automation_needed=data.get('automation_needed', 'TBD'),
            steps=data.get('steps', []),
            tags=data.get('tags', []),
            priority=data.get('priority', 'Normal'),
            metadata=data.get('metadata', {})
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

        response_data = {
            "status": "success",
            "test_case": test_case.dict(),
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
            return jsonify({"error": "Search query is required"}), 400

        logger.info(f"Searching test cases with query: {query}")

        # Get Weaviate client from app context
        weaviate_client = current_app.config.get('weaviate_client')

        if not weaviate_client or not weaviate_client.is_healthy():
            logger.warning("Weaviate client not available for search")
            return jsonify({
                "status": "error",
                "message": "Search service temporarily unavailable",
                "results": []
            }), 200

        results = weaviate_client.search_test_cases(query)
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
        }), 200

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