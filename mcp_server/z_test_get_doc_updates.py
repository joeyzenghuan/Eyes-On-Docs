import json
import asyncio

# 假设 get_doc_updates 是你要测试的函数，实际请根据你的项目导入
from eyesondocs_mcp_server import get_doc_updates

# def get_doc_updates(product, language, page, update_type):
#     # 这里是模拟返回，实际请替换为真实接口调用
#     return {
#         "product": product,
#         "language": language,
#         "page": page,
#         "update_type": update_type,
#         "result": "这是模拟返回，请替换为真实接口调用结果"
#     }

async def main():
    params = {
        "product": "AOAI-V2",
        "language": "Chinese",
        "page": 1,
        "update_type": "single"
    }
    result = await get_doc_updates(**params)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 