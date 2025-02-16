from integrations.weaviate_integration import WeaviateIntegration
from weaviate.classes.query import MetadataQuery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_test_cases():
    client = WeaviateIntegration()
    try:
        # Get all test cases
        collection = client.client.collections.get("TestCase")
        response = collection.query.get(
            return_properties=[
                "name", "description", "steps", 
                "expected_results", "tags", "priority"
            ]
        )
        
        if response.objects:
            logger.info(f"Found {len(response.objects)} test cases:")
            for obj in response.objects:
                logger.info("-" * 50)
                logger.info(f"Name: {obj.properties['name']}")
                logger.info(f"Description: {obj.properties['description']}")
                logger.info(f"Steps: {obj.properties.get('steps', [])}")
        else:
            logger.info("No test cases found in database")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    verify_test_cases() 