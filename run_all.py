import subprocess
import sys
import time
import webbrowser
import os
from dotenv import load_dotenv
import logging
import importlib

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Simplified format
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = {
        'flask': 'flask',
        'python-dotenv': 'dotenv',
        'crewai': 'crewai',
        'weaviate-client': 'weaviate',
        'openai': 'openai',
        'pydantic': 'pydantic'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
            print(f"✅ {package_name}")  # Simplified log
        except ImportError:
            print(f"❌ {package_name}")  # Simplified log
            missing_packages.append(package_name)
    
    if missing_packages:
        logger.info("Installing missing packages...")
        try:
            for package in missing_packages:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            logger.info("Successfully installed missing packages")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install packages: {str(e)}")
            return False
    
    return True

def check_env_vars():
    """Check if all required environment variables are set"""
    load_dotenv()
    required_vars = [
        'OPENAI_API_KEY',
        'WEAVIATE_URL',
        'WEAVIATE_API_KEY'
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"Missing required environment variable: {var}")
            return False
    return True

def main():
    # Check dependencies first
    if not check_dependencies():
        logger.error("Failed to install required packages. Please install them manually:")
        logger.error("pip install -r requirements.txt")
        return
    
    # Now that dependencies are installed, we can import dotenv
    from dotenv import load_dotenv
    
    # Check environment variables
    if not check_env_vars():
        logger.error("Missing environment variables. Please check .env file.")
        return
    
    try:
        # Start Flask application
        logger.info("Starting Flask application...")
        flask_process = subprocess.Popen([sys.executable, 'app.py'])
        
        # Wait for server to start
        time.sleep(3)
        
        # Open browser
        logger.info("Opening browser...")
        webbrowser.open('http://localhost:5000')
        
        # Keep the script running
        flask_process.wait()
        
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        flask_process.terminate()
        flask_process.wait()
    except Exception as e:
        logger.error(f"Error running application: {str(e)}")
        if 'flask_process' in locals():
            flask_process.terminate()
            flask_process.wait()

if __name__ == "__main__":
    main() 