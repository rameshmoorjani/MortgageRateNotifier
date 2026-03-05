

import openai
import os

# Load API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not set in environment.")
client = openai.OpenAI(api_key=api_key)
models = client.models.list()
for m in models.data:
    print(m.id)
