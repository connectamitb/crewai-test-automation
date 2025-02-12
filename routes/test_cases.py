"""Routes for test case management"""
import logging
from flask import Blueprint, request, jsonify
from testai.agents.test_case_mapping import TestCaseMappingAgent
from testai.agents.requirement_input import RequirementInputAgent, RequirementInput
from testai.agents.nlp_parsing import NLPParsingAgent
from integrations.weaviate_integration import WeaviateIntegration
from integrations.zephyr_integration import ZephyrIntegration

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
test_cases_bp = Blueprint('test_cases', __name__)

# Initialize agents
requirement_agent = RequirementInputAgent()
nlp_agent = NLPParsingAgent()
test_case_mapping_agent = TestCaseMappingAgent()

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

        requirement_text = data['requirement']
        logger.info(f"Processing requirement: {requirement_text}")

        # Step 1: Process requirement through requirement agent
        try:
            requirement = RequirementInput(
                raw_text=requirement_text,
                project_key=data.get('project_key')
            )
            logger.debug(f"Created requirement input: {requirement}")

            processed_req = requirement_agent.execute_task({
                'raw_text': requirement.raw_text,
                'project_key': requirement.project_key
            })
            logger.debug(f"Processed requirement result: {processed_req}")

            if not processed_req.get('status') == 'success':
                logger.error(f"Requirement processing failed: {processed_req}")
                return jsonify({"error": "Failed to process requirement"}), 400

            logger.info("Successfully processed requirement")

        except Exception as e:
            logger.error(f"Error in requirement processing: {str(e)}", exc_info=True)
            return jsonify({"error": f"Requirement processing error: {str(e)}"}), 500

        # Step 2: Parse requirement through NLP agent
        try:
            logger.debug(f"Sending to NLP agent: {processed_req['processed_requirement']['text']}")
            parsed_req = nlp_agent.execute_task({
                'cleaned_requirement': processed_req['processed_requirement']['text']
            })
            logger.debug(f"NLP parsing result: {parsed_req}")

            if not parsed_req.get('status') == 'success':
                logger.error(f"NLP parsing failed: {parsed_req}")
                return jsonify({"error": "Failed to parse requirement"}), 400

            logger.info("Successfully parsed requirement through NLP")

        except Exception as e:
            logger.error(f"Error in NLP parsing: {str(e)}", exc_info=True)
            return jsonify({"error": f"NLP parsing error: {str(e)}"}), 500

        # Step 3: Generate test case using mapping agent
        try:
            logger.debug(f"Sending to test case mapping agent: {parsed_req['parsed_requirement']}")
            test_case = test_case_mapping_agent.execute_task({
                'requirement': parsed_req['parsed_requirement']
            })
            logger.debug(f"Test case mapping result: {test_case}")

            if not test_case or 'test_case' not in test_case:
                logger.error(f"Test case mapping failed: {test_case}")
                return jsonify({"error": "Failed to generate test case"}), 500

            logger.info("Successfully generated test case")
            logger.info(f"Storage status: {test_case.get('storage', {})}")

            # Format response
            response = {
                "status": "success",
                "test_case": test_case['test_case'],
                "storage_status": test_case.get('storage', {})
            }

            return jsonify(response), 201

        except Exception as e:
            logger.error(f"Error in test case mapping: {str(e)}", exc_info=True)
            return jsonify({"error": f"Test case generation error: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"General error in generate_test_case: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@test_cases_bp.route('/test-cases/search', methods=['GET'])
def search_test_cases():
    """Search for test cases using vector similarity search"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({"error": "Search query is required"}), 400

        logger.info(f"Received search request with query: {query}")

        # Initialize Weaviate client if not already initialized
        weaviate_client = WeaviateIntegration()

        # Search using the test case mapping agent which handles both vector and memory search
        logger.info("Executing search using test case mapping agent...")
        results = test_case_mapping_agent.query_test_cases(query)

        logger.info(f"Found {len(results)} test cases matching query: {query}")
        logger.debug(f"Search results: {results}")

        return jsonify({
            "status": "success",
            "results": results,
            "total": len(results)
        }), 200

    except Exception as e:
        logger.error(f"Error searching test cases: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@test_cases_bp.route('/test-cases/<name>', methods=['GET'])
def get_test_case(name):
    """Get a test case by name"""
    try:
        weaviate_client = WeaviateIntegration()
        result = weaviate_client.get_test_case_by_name(name)

        if result is None:
            return jsonify({"error": "Test case not found"}), 404

        return jsonify({"status": "success", "test_case": result}), 200

    except Exception as e:
        logger.error(f"Error retrieving test case: {str(e)}")
        return jsonify({"error": str(e)}), 500

def init_integrations():
    """Initialize integration clients"""
    global weaviate_client, zephyr_client

    logger.info("Initializing integrations...")
    try:
        # Initialize Weaviate
        weaviate_client = WeaviateIntegration()
        logger.info("Successfully initialized Weaviate integration")

        # Initialize Zephyr Scale
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