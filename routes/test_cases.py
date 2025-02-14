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
        data = request.get_json()
        if not data or 'requirement' not in data:
            return jsonify({'error': 'Missing requirement field'}), 400

        logger.debug("Processing requirement: %s", data['requirement'])

        # Parse the input text
        lines = data['requirement'].split('\n')
        name = next((line for line in lines if line.strip()), "Test Case")

        # Extract steps and expected results from the requirement text
        steps = []
        expected_results = []

        for line in lines:
            if line.lower().startswith("step:"):
                steps.append(line.replace("step:", "").strip())
            elif line.lower().startswith("expected result:"):
                expected_results.append(line.replace("expected result:", "").strip())

        # If no explicit steps/results found, create basic login steps
        if not steps:
            steps = ["Navigate to login page", "Enter credentials", "Click login button"]
        if not expected_results:
            expected_results = ["Login page displayed", "Credentials accepted", "User logged in"]

        # Create a simple test case
        test_case = TestCase(
            name=name,
            description=data['requirement'],
            steps=steps,
            expected_results=expected_results
        )

        # Get Weaviate client
        weaviate_client = current_app.config.get('weaviate_client')
        if not weaviate_client:
            return jsonify({
                'status': 'error',
                'message': 'Storage service not initialized'
            }), 503

        # Store the test case
        case_id = weaviate_client.store_test_case(test_case)
        if case_id:
            logger.info("Successfully stored test case with ID: %s", case_id)
            return jsonify({
                'status': 'success',
                'message': 'Test case created successfully',
                'test_case': {
                    'name': test_case.name,
                    'description': test_case.description,
                    'steps': test_case.steps,
                    'expected_results': test_case.expected_results
                }
            }), 201
        else:
            logger.error("Failed to store test case")
            return jsonify({
                'status': 'error',
                'message': 'Failed to store test case'
            }), 500

    except Exception as e:
        logger.error("Error creating test case: %s", str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500

@test_cases_bp.route('/api/v1/test-cases/search', methods=['GET'])
def search_test_cases():
    """Search for test cases"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({
                "status": "error",
                "message": "Search query is required"
            }), 400

        weaviate_client = current_app.config.get('weaviate_client')
        if not weaviate_client:
            return jsonify({
                "status": "error",
                "message": "Search service not available"
            }), 503

        results = weaviate_client.search_test_cases(query)
        return jsonify({
            "status": "success",
            "results": results
        })

    except Exception as e:
        logger.error("Search error: %s", str(e))
        return jsonify({
            "status": "error",
            "message": str(e)
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