"""Routes for test case management"""
import logging
from flask import Blueprint, request, jsonify
from integrations.models import TestCase
from integrations.weaviate_integration import WeaviateIntegration
from integrations.zephyr_integration import ZephyrIntegration, ZephyrTestCase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
test_cases_bp = Blueprint('test_cases', __name__)

# Initialize integrations with error handling
weaviate_client = None
zephyr_client = None

def init_integrations():
    """Initialize integration clients"""
    global weaviate_client, zephyr_client
    try:
        weaviate_client = WeaviateIntegration()
        zephyr_client = ZephyrIntegration()
        logger.info("Successfully initialized Weaviate and Zephyr integrations")
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
    """Create a new test case and sync to both Weaviate and Zephyr Scale"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Create Weaviate test case
        weaviate_test_case = TestCase(**data)
        weaviate_id = weaviate_client.store_test_case(weaviate_test_case)

        # Create Zephyr test case
        zephyr_test_case = ZephyrTestCase(
            name=data["name"],
            objective=data["objective"],
            precondition=data.get("precondition", ""),
            steps=[{
                "step": step["step"],
                "test_data": step.get("test_data", ""),
                "expected_result": step.get("expected_result", "")
            } for step in data["steps"]],
            priority="Normal",
            labels=["automated", "weaviate-synced"]
        )
        zephyr_key = zephyr_client.create_test_case(zephyr_test_case)

        return jsonify({
            "message": "Test case created successfully",
            "weaviate_id": weaviate_id,
            "zephyr_key": zephyr_key
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