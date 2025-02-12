"""Routes for test case management"""
import logging
from flask import Blueprint, request, jsonify
from integrations.models import TestCase
from integrations.weaviate_integration import WeaviateIntegration
from integrations.zephyr_integration import ZephyrIntegration, ZephyrTestCase
from agents.requirement_input import RequirementInputAgent, RequirementInput
from agents.nlp_parsing import NLPParsingAgent

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
test_cases_bp = Blueprint('test_cases', __name__)

# Initialize agents and integrations
weaviate_client = None
zephyr_client = None
requirement_agent = RequirementInputAgent()
nlp_agent = NLPParsingAgent()

def init_integrations():
    """Initialize integration clients"""
    global weaviate_client, zephyr_client
    try:
        if not weaviate_client:
            weaviate_client = WeaviateIntegration()
            logger.info("Successfully initialized Weaviate integration")

        if not zephyr_client:
            zephyr_client = ZephyrIntegration()
            logger.info("Successfully initialized Zephyr integration")

        return True
    except Exception as e:
        logger.error(f"Error initializing integrations: {str(e)}")
        return False

@test_cases_bp.before_request
def ensure_integrations():
    """Ensure integrations are initialized before each request"""
    if not weaviate_client or not zephyr_client:
        if not init_integrations():
            return jsonify({"error": "Failed to initialize integrations"}), 500

@test_cases_bp.route('/test-cases', methods=['POST'])
def create_test_case():
    """Create test cases from requirements and sync to both Weaviate and Zephyr Scale"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Process requirements through agents
        requirement = RequirementInput(
            raw_text=data.get("requirement_text", ""),
            wireframe_paths=data.get("wireframe_paths", []),
            project_key=data.get("project_key")
        )

        # Clean and parse requirements
        cleaned_req = requirement_agent.clean_requirement(requirement)
        parsed_test_case = nlp_agent.parse_requirement(cleaned_req)

        # Create Weaviate test case
        weaviate_test_case = TestCase(
            name=parsed_test_case.name,
            objective=parsed_test_case.objective,
            precondition=parsed_test_case.precondition,
            automation_needed=parsed_test_case.automation_needed,
            steps=parsed_test_case.steps
        )
        weaviate_id = weaviate_client.store_test_case(weaviate_test_case)
        logger.debug(f"Stored test case in Weaviate with ID: {weaviate_id}")

        # Create Zephyr test case
        zephyr_test_case = ZephyrTestCase(
            name=parsed_test_case.name,
            objective=parsed_test_case.objective,
            precondition=parsed_test_case.precondition,
            steps=parsed_test_case.steps,
            priority="Normal",
            labels=["automated", "weaviate-synced"]
        )
        zephyr_key = zephyr_client.create_test_case(zephyr_test_case)
        logger.debug(f"Stored test case in Zephyr Scale with key: {zephyr_key}")

        return jsonify({
            "message": "Test case created successfully",
            "weaviate_id": weaviate_id,
            "zephyr_key": zephyr_key,
            "parsed_test_case": parsed_test_case.dict()
        }), 201

    except Exception as e:
        logger.error(f"Error creating test case: {str(e)}")
        return jsonify({"error": str(e)}), 400

@test_cases_bp.route('/test-cases/search', methods=['GET'])
def search_test_cases():
    """Search for test cases in both systems"""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))
        source = request.args.get('source', 'all').lower()

        results = {
            "weaviate": [],
            "zephyr": []
        }

        # Search in Weaviate
        if source in ['all', 'weaviate']:
            results["weaviate"] = weaviate_client.search_test_cases(query, limit)

        # Search in Zephyr Scale
        if source in ['all', 'zephyr']:
            results["zephyr"] = zephyr_client.search_test_cases(query, limit)

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error searching test cases: {str(e)}")
        return jsonify({"error": str(e)}), 400

@test_cases_bp.route('/test-cases/<name>', methods=['GET'])
def get_test_case(name):
    """Get a test case by name from Weaviate"""
    try:
        result = weaviate_client.get_test_case_by_name(name)
        if result is None:
            return jsonify({"error": "Test case not found"}), 404

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error retrieving test case: {str(e)}")
        return jsonify({"error": str(e)}), 400