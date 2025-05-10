from openai import AzureOpenAI
import os
from dotenv import load_dotenv
from logs import logger
# import traceback

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

load_dotenv()

AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
@retry(wait=60, stop=stop_after_attempt(1))
def chat_completion_with_backoff(**kwargs):
    return client.chat.completions.create(**kwargs)

def get_gpt_response(messages, max_tokens=1000):
    try:
        response = chat_completion_with_backoff(
            model=AZURE_OPENAI_DEPLOYMENT,  # deployment_name
            messages=messages,
            temperature=0,
            # request_timeout=300,
            max_tokens=max_tokens,
        )

        gpt_response = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        return gpt_response, prompt_tokens, completion_tokens, total_tokens
    
    except Exception as e:
        logger.exception("get_gpt_response Exception:", e)          
        return None, None, None, None



    
