import subprocess
import sys
import time
import webbrowser
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required packages are installed"""
    required = [
        'flask',
        'python-dotenv',
        'crewai',
        'weaviate-client',
        'openai',
        'pydantic',
        'pydantic-settings'
    ]
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            logger.error(f"Missing required package: {package}")
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
    # Check dependencies
    if not check_dependencies():
        logger.error("Missing dependencies. Please install required packages.")
        return
    
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