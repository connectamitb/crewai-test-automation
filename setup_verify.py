import importlib
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
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
            print(f"✅ {package}")  # Simplified log
        except ImportError as e:
            print(f"❌ {package}")  # Simplified log
            return False
    return True

def verify_env_vars():
    """Check if all required environment variables are set"""
    load_dotenv()
    required_vars = [
        'OPENAI_API_KEY',  # Only checking for OpenAI key for now
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