import os
from dotenv import load_dotenv
from openai import OpenAI

def verify_openai():
    """Verify OpenAI API key is working"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI client with API key
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Test API with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print("✅ OpenAI API key is working")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API key error: {str(e)}")
        return False

if __name__ == "__main__":
    verify_openai() 