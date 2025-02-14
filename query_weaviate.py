"""Script to query Weaviate directly and show all stored test cases."""
import logging
from integrations.weaviate_integration import WeaviateIntegration

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def list_all_test_cases():
    """List all test cases stored in Weaviate"""
    try:
        client = WeaviateIntegration()
        
        # Query all test cases
        result = (
            client.client.query
            .get("TestCase", ["name", "description", "steps", "expectedResults"])
            .do()
        )
        
        if result and "data" in result and "Get" in result["data"]:
            test_cases = result["data"]["Get"]["TestCase"]
            logger.info("Found %d test cases:", len(test_cases))
            
            for case in test_cases:
                logger.info("\n=== Test Case ===")
                logger.info("Name: %s", case.get('name'))
                logger.info("Description: %s", case.get('description'))
                logger.info("Steps: %s", case.get('steps'))
                logger.info("Expected Results: %s", case.get('expectedResults'))
                logger.info("================\n")
        else:
            logger.info("No test cases found in Weaviate")
            
    except Exception as e:
        logger.error("Error querying Weaviate: %s", str(e))

if __name__ == "__main__":
    list_all_test_cases()
