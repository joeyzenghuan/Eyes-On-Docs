import os
import openai
openai.api_type = "azure"
openai.api_base = "https://ryanopenaicandaeast.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = "*****"

response = openai.ChatCompletion.create(
  engine="gpt432k",
  messages = [{"role":"system","content":"You are an AI assistant that helps people find information."},{"role":"user","content":"hi"}],
 )