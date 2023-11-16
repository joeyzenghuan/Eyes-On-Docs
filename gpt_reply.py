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
        try:
            response = openai.ChatCompletion.create(
                engine=deployment_name,  # engine = "deployment_name".
                messages=messages,
                temperature=0,
            )

            gpt_response = response["choices"][0]["message"]["content"]
            prompt_tokens = response["usage"]["prompt_tokens"]
            completion_tokens = response["usage"]["completion_tokens"]
            total_tokens = response["usage"]["total_tokens"]
            return gpt_response, prompt_tokens, completion_tokens, total_tokens
        
        except Exception as e:
            print("get_gpt_response Exception:", e)
            return None, None, None, None


    
