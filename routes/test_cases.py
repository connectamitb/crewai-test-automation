"""Routes for test case management"""
import logging
from flask import Blueprint, request, jsonify, current_app
from integrations.models import TestCase, TestFormat
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

        requirement_text = data['requirement']
        logger.debug("Creating test case with requirement: %s", requirement_text[:50])

        # Create test format structure
        test_format = TestFormat(
            given=[
                "Valid user account exists in the system",
                "User has correct email and password",
                "System is accessible via web browser"
            ],
            when=[
                "User navigates to the login page",
                "User enters valid email and password",
                "User clicks the login button"
            ],
            then=[
                "System validates email format",
                "System validates password requirements",
                "User is successfully logged in",
                "User is redirected to dashboard",
                "Session is created for the user"
            ]
        )

        # Create test case with proper structure
        test_case = TestCase(
            name=data.get('project_key', 'Login Feature Test'),
            objective=requirement_text[:200],
            precondition="Valid user account exists and system is accessible",
            steps=[
                "Navigate to login page",
                "Enter valid credentials",
                "Submit login form",
                "Verify successful login",
                "Verify dashboard redirect"
            ],
            requirement=requirement_text,
            gherkin="""Feature: User Login Authentication

              Scenario: Successful login with valid credentials
                Given valid user account exists in the system
                And user has correct email and password
                And system is accessible via web browser
                When user navigates to the login page
                And enters valid email and password
                And clicks the login button
                Then system validates the credentials
                And user is successfully logged in
                And user is redirected to dashboard""".strip(),
            format=test_format
        )

        try:
            logger.debug("Creating test case with data: %s", data)
            weaviate_client = current_app.config.get('weaviate_client')

            if not weaviate_client:
                logger.error("Weaviate client not initialized")
                return jsonify({
                    'status': 'error',
                    'message': 'Vector storage service not initialized',
                }), 503

            if not weaviate_client.is_healthy():
                logger.error("Weaviate client not healthy")
                return jsonify({
                    'status': 'error',
                    'message': 'Vector storage service unhealthy',
                }), 503

            try:
                case_id = weaviate_client.store_test_case(test_case)
                logger.info("Successfully created and stored test case with ID: %s", case_id)
                return jsonify({
                    'status': 'success',
                    'message': 'Test case created and stored successfully',
                    'test_case': test_case.model_dump(),
                    'id': case_id
                }), 201
            except ValueError as ve:
                logger.error("Failed to store test case: %s", str(ve))
                return jsonify({
                    'status': 'error',
                    'message': str(ve)
                }), 500

        except Exception as e:
            logger.error("Error during test case storage: %s", str(e), exc_info=True)
            return jsonify({'error': str(e)}), 500

    except Exception as e:
        logger.error("Error creating test case: %s", str(e), exc_info=True)
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

        logger.debug("Executing search with Weaviate client")
        results = weaviate_client.search_test_cases(query)
        logger.info(f"Found {len(results)} test cases")
        logger.debug(f"Search results: {results}")

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