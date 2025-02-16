"""Routes for test case management"""
import logging
import os
from flask import Blueprint, request, jsonify, current_app, render_template
from agents.requirement_input import RequirementInput, RequirementInputAgent
from agents.nlp_parsing import NLPParsingAgent
from integrations.models import TestCase
from integrations.weaviate_integration import WeaviateIntegration
from weaviate.classes.query import MetadataQuery

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
test_cases_bp = Blueprint('test_cases', __name__)

@test_cases_bp.route('/api/v1/test-cases', methods=['POST'])
def create_test_case():
    """Generate and store test case from requirement"""
    try:
        data = request.get_json()
        if not data or 'requirement' not in data:
            return jsonify({'error': 'Requirement is required'}), 400

        # Initialize agents and client
        requirement_agent = RequirementInputAgent()
        nlp_agent = NLPParsingAgent()
        weaviate_client = WeaviateIntegration()

        # 1. Clean requirement
        req_input = RequirementInput(raw_text=data['requirement'])
        cleaned_req = requirement_agent.clean_requirement(req_input)
        logger.info(f"Cleaned requirement: {cleaned_req.title}")

        # 2. Generate test case
        parsed_case = nlp_agent.parse_requirement(cleaned_req)
        logger.info(f"Generated test case: {parsed_case.name}")

        # 3. Convert to TestCase model
        test_case = TestCase(
            name=parsed_case.name,
            description=parsed_case.objective,
            requirement=cleaned_req.description,
            precondition=parsed_case.precondition,
            steps=[step.step for step in parsed_case.steps],
            expected_results=parsed_case.expected_results,
            priority="High",
            tags=["security", "authentication"],
            automation_status="Not Started" if not parsed_case.automation_needed else "Recommended"
        )

        # 4. Store in Weaviate
        case_id = weaviate_client.store_test_case(test_case.to_weaviate_format())
        if not case_id:
            return jsonify({'error': 'Failed to store test case'}), 500

        return jsonify({
            'message': 'Test case created successfully',
            'test_case': {
                'id': case_id,
                'name': test_case.name,
                'description': test_case.description,
                'steps': test_case.steps,
                'expected_results': test_case.expected_results,
                'priority': test_case.priority,
                'automation_status': test_case.automation_status
            }
        }), 201

    except Exception as e:
        logger.error(f"Error creating test case: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@test_cases_bp.route('/api/v1/test-cases/search')
def search_test_cases():
    """Search for test cases"""
    try:
        query = request.args.get('q')
        if not query:
            return jsonify({'error': 'Search query is required'}), 400

        weaviate_client = WeaviateIntegration()
        collection = weaviate_client.client.collections.get("TestCase")

        # Perform semantic search
        response = collection.query.near_text(
            query=query,
            limit=5,
            return_metadata=MetadataQuery(distance=True),
            return_properties=[
                "name", "description", "steps", 
                "expected_results", "tags", "priority"
            ]
        )

        results = []
        if response.objects:
            for obj in response.objects:
                results.append({
                    'name': obj.properties['name'],
                    'description': obj.properties['description'],
                    'steps': obj.properties['steps'],
                    'expected_results': obj.properties.get('expected_results', []),
                    'tags': obj.properties.get('tags', []),
                    'priority': obj.properties.get('priority', 'Medium'),
                    'relevance_score': 1 - obj.metadata.distance
                })

        return jsonify({
            'results': results,
            'total': len(results)
        }), 200

    except Exception as e:
        logger.error(f"Error searching test cases: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# Optional: Get specific test case
@test_cases_bp.route('/api/v1/test-cases/<case_id>', methods=['GET'])
def get_test_case(case_id):
    """Get a specific test case by ID"""
    try:
        weaviate_client = WeaviateIntegration()
        test_case = weaviate_client.get_test_case(case_id)
        
        if not test_case:
            return jsonify({'error': 'Test case not found'}), 404

        return jsonify(test_case), 200

    except Exception as e:
        logger.error(f"Error retrieving test case: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@test_cases_bp.route('/test-cases', methods=['GET'])
def test_cases_page():
    """Render test cases management page"""
    return render_template('test_cases.html')