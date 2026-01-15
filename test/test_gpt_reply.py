"""
测试 gpt_reply.py 模块 - 使用 Azure OpenAI v1 API

测试内容:
1. test_basic_chat: 基本对话测试
2. test_commit_patch_summary: 提交摘要测试
3. test_structured_output: Structured Output 测试
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gpt_reply import get_gpt_response, get_gpt_structured_response
import toml


def test_basic_chat():
    """测试基本的对话功能"""
    print("\n" + "="*50)
    print("测试 1: 基本对话测试")
    print("="*50)
    
    messages = [
        {"role": "system", "content": "Assistant is a large language model trained by OpenAI."},
        {"role": "user", "content": "写一篇100字的关于春天的作文"},
    ]
    gpt_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages)
    
    print("Response:\n", gpt_response)
    print(f"Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}, Total tokens: {total_tokens}")
    
    assert gpt_response is not None, "GPT response should not be None"
    assert prompt_tokens is not None, "Prompt tokens should not be None"
    assert completion_tokens is not None, "Completion tokens should not be None"
    assert total_tokens is not None, "Total tokens should not be None"
    
    print("✅ 基本对话测试通过!")
    return True


def test_commit_patch_summary():
    """测试提交摘要功能"""
    print("\n" + "="*50)
    print("测试 2: 提交摘要测试")
    print("="*50)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "prompts.toml")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        data = toml.load(f)
    
    gpt_summary_prompt = data['gpt_summary_prompt_v2']['prompt']
    content = "Here are the commit patch data. ###From 63ab2683fc245f753d7ecd13152bcf0a95b138f4 ... openai发布gpt-66 AGI大模型 ..."
    
    messages = [
        {"role": "system", "content": gpt_summary_prompt},
        {"role": "user", "content": content},
    ]
    gpt_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages)
    
    print("Summary Response:\n", gpt_response)
    print(f"Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}, Total tokens: {total_tokens}")
    
    assert gpt_response is not None, "GPT response should not be None"
    assert prompt_tokens is not None, "Prompt tokens should not be None"
    assert completion_tokens is not None, "Completion tokens should not be None"
    assert total_tokens is not None, "Total tokens should not be None"
    
    print("✅ 提交摘要测试通过!")
    return True


def test_structured_output():
    """测试 Structured Output 功能"""
    print("\n" + "="*50)
    print("测试 3: Structured Output 测试")
    print("="*50)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant that extracts information."},
        {"role": "user", "content": "Extract the name and age from: John is 25 years old and lives in New York."},
    ]
    
    # 定义 JSON Schema 格式
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "person_info",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The person's name"
                    },
                    "age": {
                        "type": "integer",
                        "description": "The person's age"
                    },
                    "city": {
                        "type": "string",
                        "description": "The city where the person lives"
                    }
                },
                "required": ["name", "age", "city"],
                "additionalProperties": False
            }
        }
    }
    
    parsed_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_structured_response(
        messages, response_format
    )
    
    print("Parsed Response:", json.dumps(parsed_response, indent=2, ensure_ascii=False))
    print(f"Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}, Total tokens: {total_tokens}")
    
    assert parsed_response is not None, "Parsed response should not be None"
    assert isinstance(parsed_response, dict), "Parsed response should be a dictionary"
    assert "name" in parsed_response, "Response should contain 'name'"
    assert "age" in parsed_response, "Response should contain 'age'"
    assert "city" in parsed_response, "Response should contain 'city'"
    assert prompt_tokens is not None, "Prompt tokens should not be None"
    
    print(f"提取的信息: 姓名={parsed_response['name']}, 年龄={parsed_response['age']}, 城市={parsed_response['city']}")
    print("✅ Structured Output 测试通过!")
    return True


def test_api_connection():
    """测试 API 连接是否正常 (快速测试)"""
    print("\n" + "="*50)
    print("测试 0: API 连接测试")
    print("="*50)
    
    messages = [
        {"role": "user", "content": "Say 'Hello' in one word."},
    ]
    gpt_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages, max_tokens=10)
    
    if gpt_response is not None:
        print(f"API 连接正常! 响应: {gpt_response}")
        print("✅ API 连接测试通过!")
        return True
    else:
        print("❌ API 连接失败，请检查环境变量配置:")
        print("  - AZURE_OPENAI_KEY")
        print("  - AZURE_OPENAI_ENDPOINT")
        print("  - AZURE_OPENAI_DEPLOYMENT")
        return False


if __name__ == "__main__":
    print("="*50)
    print("gpt_reply.py 测试套件 (Azure OpenAI v1 API)")
    print("="*50)
    
    # 首先测试 API 连接
    if not test_api_connection():
        print("\n❌ API 连接失败，跳过后续测试")
        sys.exit(1)
    
    # 运行所有测试
    all_passed = True
    
    try:
        test_basic_chat()
    except AssertionError as e:
        print(f"❌ 基本对话测试失败: {e}")
        all_passed = False
    except Exception as e:
        print(f"❌ 基本对话测试异常: {e}")
        all_passed = False
    
    try:
        test_commit_patch_summary()
    except AssertionError as e:
        print(f"❌ 提交摘要测试失败: {e}")
        all_passed = False
    except Exception as e:
        print(f"❌ 提交摘要测试异常: {e}")
        all_passed = False
    
    try:
        test_structured_output()
    except AssertionError as e:
        print(f"❌ Structured Output 测试失败: {e}")
        all_passed = False
    except Exception as e:
        print(f"❌ Structured Output 测试异常: {e}")
        all_passed = False
    
    # 输出总结
    print("\n" + "="*50)
    if all_passed:
        print("🎉 所有测试通过!")
    else:
        print("⚠️ 部分测试失败，请检查上面的错误信息")
    print("="*50)