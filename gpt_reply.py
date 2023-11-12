import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("AZURE_OPENAI_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
# logger.debug(f"AZURE_OPENAI_KEY: {AZURE_OPENAI_KEY}")
openai.api_type = "azure"
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")

def get_gpt_response(messages):
        response = openai.ChatCompletion.create(
            engine=deployment_name,  # engine = "deployment_name".
            messages=messages,
            temperature=0,
        )
        return response

    
