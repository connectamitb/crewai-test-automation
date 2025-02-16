import os
import sys
import logging
from dotenv import load_dotenv
import weaviate
from weaviate.classes.init import Auth, AdditionalConfig, Timeout
from weaviate.collections.classes.config import (
    Configure, 
    Property,
    DataType
)
from weaviate.classes.query import MetadataQuery

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    client = None
    try:
        # Step 1: Load environment variables
        load_dotenv()
        weaviate_url = os.getenv("WEAVIATE_URL")
        weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not all([weaviate_url, weaviate_api_key, openai_api_key]):
            raise ValueError("Missing required environment variables")
        logger.info("Environment variables loaded successfully")

        # Step 2: Connect to Weaviate Cloud using v4 API
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=Auth.api_key(weaviate_api_key),
            headers={
                "X-OpenAI-Api-Key": openai_api_key
            },
            additional_config=AdditionalConfig(
                timeout=Timeout(
                    init=30,    # Connection timeout
                    query=60,   # Query operations timeout
                    insert=120  # Insert operations timeout
                )
            )
        )
        
        if client.is_ready():
            logger.info("✅ Connected to Weaviate Cloud successfully")
        else:
            raise Exception("Weaviate Cloud instance is not ready")

        # Step 3: Create schema
        collections = client.collections.list_all()
        if "TestCase" in collections:
            logger.info("Deleting existing TestCase collection...")
            client.collections.delete("TestCase")
        
        # Create new collection
        client.collections.create(
            name="TestCase",
            description="Test case collection for storing automated tests",
            vectorizer_config=Configure.Vectorizer.text2vec_openai(),
            properties=[
                Property(
                    name="name",
                    data_type=DataType.TEXT,
                    description="Name of the test case"
                ),
                Property(
                    name="description",
                    data_type=DataType.TEXT,
                    description="Description of what the test verifies"
                ),
                Property(
                    name="steps",
                    data_type=DataType.TEXT_ARRAY,
                    description="List of test steps to execute"
                ),
                Property(
                    name="expected_results",
                    data_type=DataType.TEXT_ARRAY,
                    description="Expected results for each test step"
                )
            ]
        )
        logger.info("✅ Schema created successfully")

        # Step 4: Insert sample test case
        test_case = {
            "name": "Login Test",
            "description": "Verify user can login with valid credentials",
            "steps": [
                "Navigate to login page",
                "Enter valid username and password",
                "Click login button"
            ],
            "expected_results": [
                "Login page loads successfully",
                "Credentials are accepted",
                "User is redirected to dashboard"
            ]
        }
        
        # Insert using the v4 API
        collection = client.collections.get("TestCase")
        result = collection.data.insert(test_case)
        logger.info(f"✅ Test case inserted with ID: {result}")

        # Step 5: Verify with search
        try:
            # Get the collection
            collection = client.collections.get("TestCase")
            
            # Vector search using correct v4 syntax
            response = collection.query.near_text(
                query="login authentication",
                limit=2,
                return_metadata=MetadataQuery(distance=True),
                return_properties=["name", "description", "steps"]
            )
            
            logger.info("\n=== Search Results ===")
            if response.objects:
                for obj in response.objects:
                    logger.info(f"Name: {obj.properties['name']}")
                    logger.info(f"Description: {obj.properties['description']}")
                    logger.info(f"Steps: {obj.properties['steps']}")
                    logger.info(f"Distance: {obj.metadata.distance}")
                    logger.info("---")
            else:
                logger.info("No results found")

            logger.info("✅ All operations completed successfully")

        except Exception as e:
            logger.error(f"❌ Operation failed: {e}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Operation failed: {e}")
        sys.exit(1)
    finally:
        # Ensure client is properly closed
        if client:
            client.close()

if __name__ == "__main__":
    main() 