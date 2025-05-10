import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gpt_reply import get_gpt_response
import toml

def test_basic_chat():
    messages = [
        {"role": "system", "content": "Assistant is a large language model trained by OpenAI."},
        {"role": "user", "content": "写一篇100字的关于春天的作文"},
    ]
    gpt_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages)
    print("Response:\n", gpt_response)
    print(f"Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}, Total tokens: {total_tokens}")
    assert gpt_response is not None
    assert prompt_tokens is not None
    assert completion_tokens is not None
    assert total_tokens is not None

def test_commit_patch_summary():
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
    assert gpt_response is not None
    assert prompt_tokens is not None
    assert completion_tokens is not None
    assert total_tokens is not None

if __name__ == "__main__":
    test_basic_chat()
    test_commit_patch_summary()