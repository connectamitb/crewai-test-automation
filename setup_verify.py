import importlib
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_installation():
    packages = [
        'flask',
        'dotenv',
        'crewai',
        'weaviate',
        'openai',
        'pydantic',
        'langchain'
    ]
    
    for package in packages:
        try:
            importlib.import_module(package)
            logger.info(f"✅ {package} installed successfully")
        except ImportError as e:
            logger.error(f"❌ {package} not installed: {str(e)}")
            return False
    return True

def verify_env_vars():
    load_dotenv()
    required_vars = [
        'OPENAI_API_KEY',
        'WEAVIATE_URL',
        'WEAVIATE_API_KEY',
        'STORAGE_API_ENDPOINT',
        'ZEPHYR_SCALE_TOKEN'
    ]
    
    for var in required_vars:
        if os.getenv(var):
            logger.info(f"✅ {var} is set")
        else:
            logger.error(f"❌ {var} is not set")
            return False
    return True

if __name__ == "__main__":
    print("\nVerifying installation...")
    packages_ok = verify_installation()
    
    print("\nVerifying environment variables...")
    env_ok = verify_env_vars()
    
    if packages_ok and env_ok:
        print("\n✅ All checks passed! You can now run the application.")
    else:
        print("\n❌ Some checks failed. Please fix the issues above.") 