import requests
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

# Now you can access the environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_URL = os.getenv("OPENAI_URL")
PROXY = os.getenv("PROXY")


def get_captcha_text(encoded_image):
    question_prompt = "give me only the text of this 5 character captcha not anything else or additional response"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    message = {
        "role": "user",
        "content": [
            {"type": "text", "text": question_prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpg;base64,{encoded_image}",
                    "detail": "low",
                },
            },
        ],
    }
    payload = {
        "model": "gpt-4o-mini",
        "temperature": 0.1,
        "messages": [message],
        "max_tokens": 10,
    }
    try:
        proxies = {}
        if PROXY:
            proxies = {
                'http': PROXY,
                'https': PROXY
            }
        response = requests.post(
            f"{OPENAI_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
            proxies=proxies
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
