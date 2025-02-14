"""Routes for test case management"""
import logging
import os
from flask import Blueprint, request, jsonify, current_app
from agents.requirement_input import CleanedRequirement
from agents.nlp_parsing import NLPParsingAgent
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
        # Log environment variables (without values)
        logger.debug("Checking environment variables...")
        env_vars = ['WEAVIATE_URL', 'WEAVIATE_API_KEY', 'OPENAI_API_KEY']
        for var in env_vars:
            logger.debug(f"{var} is {'set' if os.getenv(var) else 'not set'}")

        data = request.get_json()
        logger.debug("Received request data: %s", data)

        if not data or 'requirement' not in data:
            logger.error("Missing requirement field in request data")
            return jsonify({'error': 'Missing requirement field'}), 400

        # Create cleaned requirement
        cleaned_req = CleanedRequirement(
            title="Test Case",
            description=data['requirement'],
            prerequisites=[],
            acceptance_criteria=[]
        )

        # Parse requirements into lines
        lines = data['requirement'].split('\n')
        current_section = None

        # Process each line to populate cleaned requirement
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if "Prerequisites:" in line:
                current_section = "prerequisites"
                continue
            elif "Acceptance Criteria:" in line:
                current_section = "acceptance_criteria"
                continue
            elif "Description:" in line:
                cleaned_req.description = line.replace("Description:", "").strip()
                continue
            elif not current_section and line:  # First non-empty line is title
                cleaned_req.title = line
                continue

            # Add items to appropriate section
            if current_section == "prerequisites" and line.startswith("-"):
                cleaned_req.prerequisites.append(line[1:].strip())
            elif current_section == "acceptance_criteria" and line.startswith("-"):
                cleaned_req.acceptance_criteria.append(line[1:].strip())

        logger.debug(f"Cleaned requirement: {cleaned_req}")

        # Use NLP agent to generate structured test case
        nlp_agent = NLPParsingAgent()
        parsed_test_case = nlp_agent.parse_requirement(cleaned_req)
        logger.debug(f"Parsed test case: {parsed_test_case}")

        # Convert parsed test case to storage format
        test_case = TestCase(
            name=parsed_test_case.name,
            description=parsed_test_case.objective,
            steps=[step["step"] for step in parsed_test_case.steps],
            expected_results=[step["expected_result"] for step in parsed_test_case.steps]
        )
        logger.debug("Created TestCase object: %s", test_case)

        # Get Weaviate client
        weaviate_client = current_app.config.get('weaviate_client')
        if not weaviate_client:
            logger.error("Weaviate client not found in app config")
            return jsonify({
                'status': 'error',
                'message': 'Storage service not initialized'
            }), 503

        # Check Weaviate health
        if not weaviate_client.is_healthy():
            logger.error("Weaviate client is not healthy")
            return jsonify({
                'status': 'error',
                'message': 'Storage service is not healthy'
            }), 503

        # Store the test case
        logger.debug("Attempting to store test case in Weaviate")
        case_id = weaviate_client.store_test_case(test_case)

        if case_id:
            logger.info("Successfully stored test case with ID: %s", case_id)
            return jsonify({
                'status': 'success',
                'message': 'Test case created successfully',
                'test_case': {
                    'id': case_id,
                    'name': test_case.name,
                    'description': test_case.description,
                    'steps': test_case.steps,
                    'expected_results': test_case.expected_results
                }
            }), 201
        else:
            logger.error("Failed to store test case - no ID returned")
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