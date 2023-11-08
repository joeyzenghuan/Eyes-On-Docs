# import os
# import openai
# openai.api_type = "azure"
# openai.api_base = "https://ryanopenaicandaeast.openai.azure.com/"
# openai.api_version = "2023-07-01-preview"
# openai.api_key = "*****"

# response = openai.ChatCompletion.create(
#   engine="gpt432k",
#   messages = [{"role":"system","content":"You are an AI assistant that helps people find information."},{"role":"user","content":"hi"}],
#  )


import toml

with open('prompts.toml', 'r') as f:
    data = toml.load(f)

gpt_summary_prompt_v1 = data['gpt_summary_prompt_v1']['prompt']
gpt_title_prompt_v1 = data['gpt_title_prompt_v1']['prompt']

print(f"gpt_summary_prompt_v1: {gpt_summary_prompt_v1}")
print(f"gpt_title_prompt_v1: {gpt_title_prompt_v1}")
