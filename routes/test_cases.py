"""Routes for test case management"""
import logging
from flask import Blueprint, request, jsonify, current_app
from integrations.models import TestCase
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
test_cases_bp = Blueprint('test_cases', __name__)

@test_cases_bp.route('/api/v1/test-cases', methods=['POST'])
def create_test_case():
    """Create and store a test case"""
    try:
        logger.debug("Received test case creation request")
        data = request.get_json()
        if not data:
            logger.warning("No JSON data received")
            return jsonify({'error': 'Missing request data'}), 400

        if 'requirement' not in data:
            logger.warning("Missing requirement in request data")
            return jsonify({'error': 'Missing requirement field'}), 400

        logger.debug(f"Creating test case with requirement: {data['requirement'][:50]}...")

        # Create test case with proper structure
        test_case = TestCase(
            name=f"TC_{int(time.time())}", # Unique name based on timestamp
            objective=data['requirement'][:200],  # First 200 chars as objective
            precondition="System is accessible and configured",
            steps=[
                "Navigate to the feature",
                "Perform the required action",
                "Verify the expected outcome"
            ],
            requirement=data['requirement'],
            gherkin="""Feature: Requirement Verification\n
  Scenario: Basic Verification\n
    Given the system is accessible\n
    When I perform the required action\n
    Then I should see the expected outcome""".strip()
        )

        weaviate_client = current_app.config.get('weaviate_client')
        if not weaviate_client or not weaviate_client.is_healthy():
            logger.warning("Weaviate client unavailable, storing in memory only")
            return jsonify({
                'status': 'partial_success',
                'message': 'Test case created but vector storage unavailable',
                'test_case': test_case.model_dump()
            }), 201

        case_id = weaviate_client.store_test_case(test_case)
        if not case_id:
            logger.warning("Failed to store test case in Weaviate")
            return jsonify({
                'status': 'partial_success',
                'message': 'Test case created but storage failed',
                'test_case': test_case.model_dump()
            }), 201

        logger.info(f"Successfully created and stored test case with ID: {case_id}")
        return jsonify({
            'status': 'success',
            'message': 'Test case created and stored successfully',
            'test_case': test_case.model_dump(),
            'id': case_id
        }), 201

    except Exception as e:
        logger.error(f"Error creating test case: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

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
            })

        logger.info(f"Searching test cases with query: {query}")
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

        return jsonify({
            "status": "success",
            "results": results,
            "total": len(results)
        })

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