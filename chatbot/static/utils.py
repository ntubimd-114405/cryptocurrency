# chatbot/utils.py

import openai
from django.conf import settings


openai.api_key = settings.OPENAI_API_KEY


def chat_with_gpt(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # 或 "gpt-3.5-turbo"
            messages=[
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        reply = response['choices'][0]['message']['content']
        return reply
    except Exception as e:
        return f"Error: {str(e)}"
