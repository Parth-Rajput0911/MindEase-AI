import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_wellness_response(user_message: str) -> str:
    """Sends user message to Groq and returns the AI reply."""
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are MindEase AI, a gentle, compassionate, and supportive mental wellness companion. "
                        "Provide warm, comforting advice for managing stress, practicing mindfulness, and feeling heard. "
                        "Do not provide medical diagnoses or clinical health advice."
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"LLM Error: {e}")
        return "I'm having a little trouble connecting right now. Please try again in a moment."