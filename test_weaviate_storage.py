"""Script to test Weaviate storage and semantic search with requirements."""
import logging
import os
from dotenv import load_dotenv
from integrations.weaviate_integration import WeaviateIntegration
from integrations.models import TestCase
from agents.requirement_input import RequirementInput, RequirementInputAgent
from agents.nlp_parsing import NLPParsingAgent
from weaviate.classes.query import MetadataQuery

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_requirement_to_search():
    """Test full flow: requirement -> test case -> storage -> search"""
    try:
        # Create agents and client
        requirement_agent = RequirementInputAgent()
        nlp_agent = NLPParsingAgent()
        client = WeaviateIntegration()
        logger.info("Created agents and Weaviate client")
        
        # Verify connection
        if not client.is_healthy():
            logger.error("❌ Weaviate connection is not healthy")
            return
        logger.info("✅ Weaviate connection is healthy")
        
        # Sample requirements
        requirements = [
            """Login Feature Testing
            Test the user authentication system thoroughly.
            
            Prerequisites:
            - Valid user credentials
            - Test environment access
            
            Acceptance Criteria:
            - Users can log in with valid credentials
            - Invalid credentials are rejected
            - Password reset works correctly
            - Account lockout after failed attempts""",
            
            """Password Management
            Verify password change and reset functionality.
            
            Prerequisites:
            - Existing user account
            - Email service configured
            
            Acceptance Criteria:
            - Users can change password when logged in
            - Password reset email is sent
            - New password meets security requirements
            - Old password becomes invalid"""
        ]
        
        stored_ids = []
        # Process each requirement
        for raw_requirement in requirements:
            # 1. Clean requirement
            req_input = RequirementInput(raw_text=raw_requirement)
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
            case_id = client.store_test_case(test_case.to_weaviate_format())
            if case_id:
                stored_ids.append(case_id)
                logger.info(f"✅ Test case stored with ID: {case_id}")
            else:
                logger.error("❌ Failed to store test case")

        # 5. Test semantic search
        logger.info("\nTesting semantic search:")
        collection = client.client.collections.get("TestCase")
        
        search_queries = [
            "login authentication",
            "password reset process",
            "security requirements",
            "account management"
        ]

        for query in search_queries:
            logger.info(f"\nSearching for: '{query}'")
            response = collection.query.near_text(
                query=query,
                limit=2,
                return_metadata=MetadataQuery(distance=True),
                return_properties=["name", "description", "steps", "tags", "priority"]
            )
            
            if response.objects:
                for obj in response.objects:
                    logger.info("-" * 50)
                    logger.info(f"Found: {obj.properties['name']}")
                    logger.info(f"Description: {obj.properties['description']}")
                    logger.info(f"Steps: {obj.properties['steps']}")
                    logger.info(f"Tags: {obj.properties.get('tags', [])}")
                    logger.info(f"Relevance Score: {1 - obj.metadata.distance:.2f}")
            else:
                logger.info("No results found")

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    test_requirement_to_search()
