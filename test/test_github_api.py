import requests
import os
from dotenv import load_dotenv

# 加载上级目录的 .env 文件
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

# 从环境变量获取 GitHub Token
token = os.getenv("PERSONAL_TOKEN")
# print(token)
if not token:
    raise ValueError("PERSONAL_TOKEN not found in environment variables. 请在.env文件中设置PERSONAL_TOKEN。")

# 你要测试的 API URL
url = "https://api.github.com/repos/MicrosoftDocs/azure-ai-docs/commits?path=articles/ai-services/agents"

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github+json"
}

try:
    response = requests.get(url, headers=headers)
    print("Status Code:", response.status_code)
    if response.status_code != 200:
        print("请求失败，状态码:", response.status_code)
        print("响应内容:", response.text)
    else:
        # 尝试解析为JSON
        try:
            data = response.json()
            print("返回数据类型:", type(data))
            print("返回数据预览:", data if isinstance(data, dict) else data[:2])  # 只打印前2条，避免太多
        except Exception as e:
            print("无法解析为JSON，原始返回内容：", response.text)
except Exception as e:
    print("请求异常:", e) 