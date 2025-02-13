import webbrowser
import subprocess
import time
import os
import sys

def main():
    # Start Flask application in the background
    flask_process = subprocess.Popen([sys.executable, 'app.py'])
    
    # Wait for the server to start
    time.sleep(2)
    
    # Open the browser
    webbrowser.open('http://localhost:5000')
    
    try:
        # Keep the script running
        flask_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        flask_process.terminate()
        flask_process.wait()

if __name__ == "__main__":
    main() 