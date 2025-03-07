#This file was created to test the openrouter api
from openai import OpenAI
import os
import dotenv

dotenv.load_dotenv()

#Connect to your llm api
# Load environment variables
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")

client = OpenAI(
  base_url=openrouter_api_url,
  api_key=openrouter_api_key,
)
message= "What is the capital of France?"
completion = client.chat.completions.create(
    model="meta-llama/llama-3.3-70b-instruct:free",
    messages=[{"role": "user", "content": message}],
)

print(completion.choices[0].message.content)