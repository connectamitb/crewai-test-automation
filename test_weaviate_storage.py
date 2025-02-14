"""Script to test Weaviate storage directly."""
import logging
import os
from integrations.weaviate_integration import WeaviateIntegration
from integrations.models import TestCase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_store_case():
    """Test storing a simple case in Weaviate"""
    try:
        # Create Weaviate client
        client = WeaviateIntegration()
        
        # Create a simple test case
        test_case = TestCase(
            name="Simple Login Test",
            description="Test basic login functionality",
            steps=["Navigate to login", "Enter credentials", "Click login button"],
            expected_results=["Login page shown", "Credentials accepted", "User logged in"]
        )
        
        # Store the test case
        case_id = client.store_test_case(test_case)
        
        if case_id:
            logger.info("✅ Test case stored successfully with ID: %s", case_id)
            
            # Verify by retrieving
            retrieved = client.get_test_case("Simple Login Test")
            if retrieved:
                logger.info("✅ Retrieved test case successfully:")
                logger.info("Name: %s", retrieved.get('name'))
                logger.info("Description: %s", retrieved.get('description'))
                logger.info("Steps: %s", retrieved.get('steps'))
                logger.info("Expected Results: %s", retrieved.get('expectedResults'))
            else:
                logger.error("❌ Could not retrieve stored test case")
        else:
            logger.error("❌ Failed to store test case")
            
    except Exception as e:
        logger.error("❌ Error: %s", str(e))

if __name__ == "__main__":
    test_store_case()
