import os
from google import genai
from dotenv import load_dotenv

load_dotenv("backend/.env")

api_key = os.getenv("GEMINI_API_KEY")
print("API KEY:", api_key)

try:
    client = genai.Client(api_key=api_key)
    print("Client created")
    
    for model_str in ["gemini-flash-lite-latest", "models/gemini-flash-lite-latest"]:
        try:
            response = client.models.generate_content(
                model=model_str,
                contents="Say hi"
            )
            print(f"Generated text for {model_str}:", response.text)
        except Exception as e:
            print(f"Error generating content for {model_str}:", type(e), e)
        
except Exception as e:
    print("Global error:", e)
