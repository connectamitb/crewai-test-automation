import os
from dotenv import load_dotenv
from integrations.weaviate_integration import WeaviateIntegration
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_weaviate():
    """Verify Weaviate connection and credentials"""
    weaviate_client = None
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize Weaviate client
        weaviate_client = WeaviateIntegration()
        
        # Check health
        if weaviate_client.is_healthy():
            print("✅ Weaviate connection successful")
            print("✅ Schema creation successful")
            return True
        else:
            print("❌ Weaviate health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Weaviate verification failed: {str(e)}")
        return False
    finally:
        if weaviate_client:
            weaviate_client.close()

if __name__ == "__main__":
    verify_weaviate() 