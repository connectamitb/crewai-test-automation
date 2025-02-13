import os
from openai import OpenAI

client = OpenAI()
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print("✅ OpenAI API key is working")
except Exception as e:
    print(f"❌ OpenAI API key error: {str(e)}") 