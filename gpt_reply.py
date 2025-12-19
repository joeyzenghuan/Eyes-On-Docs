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

load_dotenv(override=True)  # 允许覆盖环境变量

AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
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

def get_gpt_structured_response(messages, response_format):
    """
    使用 OpenAI structured output 获取格式化的 GPT 响应
    
    Args:
        messages: 消息列表
        response_format: 响应格式定义 (JSON schema)
        
    Returns:
        tuple: (parsed_response_dict, prompt_tokens, completion_tokens, total_tokens)
    
    Note:
        不设置max_tokens，使用OpenAI API默认行为（上下文窗口减去prompt tokens）
    """
    try:
        response = chat_completion_with_backoff(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            temperature=0,
            response_format=response_format
        )

        # structured output 返回的是 JSON 格式的字符串
        gpt_response_content = response.choices[0].message.content
        
        # 记录响应内容以便调试
        logger.debug(f"GPT structured response content: {gpt_response_content}")
        
        # 检查响应是否为空
        if not gpt_response_content:
            logger.error("GPT returned empty response content")
            return None, None, None, None
        
        # 解析 JSON 响应
        import json
        try:
            parsed_response = json.loads(gpt_response_content)
        except json.JSONDecodeError as json_error:
            logger.error(f"JSON decode error: {json_error}")
            logger.error(f"Response content that failed to parse: {gpt_response_content}")
            # 检查是否是由于响应被截断导致的
            if len(gpt_response_content) > 0 and not gpt_response_content.rstrip().endswith('}'):
                logger.error("Response appears to be truncated. Consider increasing max_tokens.")
            return None, None, None, None
        
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        
        return parsed_response, prompt_tokens, completion_tokens, total_tokens
    
    except Exception as e:
        logger.exception("get_gpt_structured_response Exception:", e)          
        return None, None, None, None



    
