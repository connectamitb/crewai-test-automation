"""Routes for test case management"""
import logging
from flask import Blueprint, request, jsonify
from testai.agents.test_case_mapping import TestCaseMappingAgent
from testai.agents.requirement_input import RequirementInputAgent, RequirementInput
from testai.agents.nlp_parsing import NLPParsingAgent
from integrations.weaviate_integration import WeaviateIntegration
from integrations.zephyr_integration import ZephyrIntegration, ZephyrTestCase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
test_cases_bp = Blueprint('test_cases', __name__)

# Initialize agents and integrations
requirement_agent = RequirementInputAgent()
nlp_agent = NLPParsingAgent()
test_case_mapping_agent = TestCaseMappingAgent()

def init_integrations():
    """Initialize integration clients"""
    global weaviate_client, zephyr_client

    logger.info("Initializing integrations...")
    try:
        weaviate_client = WeaviateIntegration()
        logger.info("Successfully initialized Weaviate integration")

        zephyr_client = ZephyrIntegration()
        logger.info("Successfully initialized Zephyr integration")

        return True
    except Exception as e:
        logger.error(f"Error initializing integrations: {str(e)}")
        return False

# Initialize integrations at module load
weaviate_client = None
zephyr_client = None
init_integrations()

@test_cases_bp.route('/generate-test-case', methods=['POST'])
def generate_test_case():
    """Generate and store test cases from requirements"""
    try:
        logger.info("Received request to generate test case")
        data = request.get_json()
        if not data or 'requirement' not in data:
            return jsonify({"error": "Requirement text is required"}), 400

        requirement_text = data['requirement']
        logger.info(f"Generating test case for requirement: {requirement_text}")

        # Step 1: Process requirement through requirement agent
        requirement = RequirementInput(
            raw_text=requirement_text,
            project_key=data.get('project_key')
        )

        processed_req = requirement_agent.execute_task({
            'raw_text': requirement.raw_text,
            'project_key': requirement.project_key
        })

        if not processed_req.get('status') == 'success':
            return jsonify({"error": "Failed to process requirement"}), 400

        # Step 2: Parse requirement through NLP agent
        parsed_req = nlp_agent.execute_task({
            'cleaned_requirement': processed_req['processed_requirement']['text']
        })

        if not parsed_req.get('status') == 'success':
            return jsonify({"error": "Failed to parse requirement"}), 400

        # Step 3: Generate test case using mapping agent
        test_case = test_case_mapping_agent.execute_task({
            'requirement': parsed_req['parsed_requirement']
        })

        if not test_case or 'test_case' not in test_case:
            return jsonify({"error": "Failed to generate test case"}), 500

        logger.info("Successfully generated test case")
        return jsonify(test_case), 201

    except Exception as e:
        logger.error(f"Error generating test case: {str(e)}")
        return jsonify({"error": str(e)}), 500

@test_cases_bp.route('/test-cases/search', methods=['GET'])
def search_test_cases():
    """Search for test cases using vector similarity search"""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))

        if not query:
            return jsonify({"error": "Search query is required"}), 400

        logger.info(f"Searching test cases with query: {query}")

        # Perform vector search in Weaviate
        weaviate_results = weaviate_client.search_test_cases(query, limit)
        logger.info(f"Found {len(weaviate_results)} results in Weaviate")

        # Format results
        formatted_results = []
        for result in weaviate_results:
            formatted_result = {
                "title": result.get("name", ""),
                "description": result.get("objective", ""),
                "steps": result.get("steps", []),
                "score": result.get("_additional", {}).get("score", 0)
            }
            formatted_results.append(formatted_result)

        return jsonify({
            "results": formatted_results,
            "total": len(formatted_results)
        }), 200

    except Exception as e:
        logger.error(f"Error searching test cases: {str(e)}")
        return jsonify({"error": str(e)}), 500

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