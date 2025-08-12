import json
import os
import sys

from dotenv import load_dotenv

load_dotenv(override=True)  # 允许覆盖环境变量


# 获取当前文件的路径
current_dir = os.path.dirname(__file__)
print(current_dir)
# 获取根目录的路径
root_dir = os.path.join(current_dir, os.pardir)
print(root_dir)
# 添加根目录到系统路径中
sys.path.append(os.path.abspath(root_dir))

from logs import logger

from azure.identity import DefaultAzureCredential
from cosmosdbservice import CosmosConversationClient

# CosmosDB Integration Settings
AZURE_COSMOSDB_DATABASE = os.getenv("AZURE_COSMOSDB_DATABASE")
AZURE_COSMOSDB_ACCOUNT = os.getenv("AZURE_COSMOSDB_ACCOUNT")
AZURE_COSMOSDB_CONVERSATIONS_CONTAINER = os.getenv(
    "AZURE_COSMOSDB_CONVERSATIONS_CONTAINER"
)
AZURE_COSMOSDB_ACCOUNT_KEY = os.getenv("AZURE_COSMOSDB_ACCOUNT_KEY")
save_commit_history_to_cosmosdb = False

# print(AZURE_COSMOSDB_DATABASE, AZURE_COSMOSDB_ACCOUNT, AZURE_COSMOSDB_CONVERSATIONS_CONTAINER)
# print(AZURE_COSMOSDB_ACCOUNT_KEY)

# Initialize a CosmosDB client with AAD auth and containers
cosmos_conversation_client = None
if (
    AZURE_COSMOSDB_DATABASE
    and AZURE_COSMOSDB_ACCOUNT
    and AZURE_COSMOSDB_CONVERSATIONS_CONTAINER
):
    save_commit_history_to_cosmosdb = True
    try:
        cosmos_endpoint = f"https://{AZURE_COSMOSDB_ACCOUNT}.documents.azure.com:443/"

        if not AZURE_COSMOSDB_ACCOUNT_KEY:
            credential = DefaultAzureCredential()
        else:
            credential = AZURE_COSMOSDB_ACCOUNT_KEY

        cosmos_conversation_client = CosmosConversationClient(
            cosmosdb_endpoint=cosmos_endpoint,
            credential=credential,
            database_name=AZURE_COSMOSDB_DATABASE,
            container_name=AZURE_COSMOSDB_CONVERSATIONS_CONTAINER,
        )
        # print(cosmos_conversation_client)
    except Exception as e:
        logger.exception("Exception in CosmosDB initialization", e)
        save_commit_history_to_cosmosdb = False
        cosmos_conversation_client = None

query = f"SELECT Top 2 c.gpt_summary_response, c.gpt_title_response, c.topic, c.language \
FROM c where c.gpt_summary_response != 'None' and c.gpt_title_response != 'None' \
 and c.language = 'Chinese' \
  and CONTAINS(c.topic, 'Cog')\
order by c.commit_time desc"

summary_vs_title = list(
    cosmos_conversation_client.container_client.query_items(
        query=query, enable_cross_partition_query=True
    )
)
## if no messages are found, return false
#   and CONTAINS(c.topic, 'Fabric')\

print(len(summary_vs_title))

import pandas as pd
from gpt_reply import get_gpt_response

# 初始化一个空列表来存储行数据
rows = []

system_message = """
You are a Title generator bot.
The input is a document change summary, which includes the link of the document and the summary of the change. The input may include change history for multiple links.
You need to generate a title for the input. There should be 3 parts in the title. Output format: "0/1 [tag] Title"
<1st part> Put 0 or 1 in the beginning of the title to indicate whether the change is an important change that need users to pay attention to.
0 means not important: the change is a minor change, such as typo fix, grammar fix, metadata change, Hyperlink change, author change, etc. 
Or the change is not parsable by the bot, such as binary file change or image change.
1 means important.
<2nd part> Generate a tag in the beginning of the title to indicate the object type of the input.
The tag should be the object type of the input.
Here are some examples of tags: Model, Quota, Time, Region, New Feature, Text, Limitation.
<3rd part> Generate a title that succinctly summarizes the input.
Only generate 1 tag and 1 title. If there are multiple topics in the input, please choose the most important one.

You need to translate the tag into specified language if the input is not in English.
Do not generate double quotes. Start from 0 or 1 directly.
"""

# old = """
# Provide a title that succinctly summarizes the input and generate a tag in the beginning. Put 0 or 1 in the beginning of the title to indicate whether the input is important change or not.
# Output format: "0 [tag] Title"
# Only generate 1 tag and 1 title. If there are multiple topics in the input, please choose the most important one.
# The tag should be the object type of the input.
# Here are some examples of tags: Model, Quota, Renaming, Image, Time, Region, New Feature, Text.
# You need to translate the tag into specified language if the input is not in English.
# """

# 使用循环来生成行数据
for i in summary_vs_title:
    messages = [
        {
            "role": "system",
            "content": system_message,
        },
        {
            "role": "user",
            "content": f"Here are the commit patch data. ###{i['gpt_summary_response']} ### Reply in Chinese",
        },
    ]
    new_title, b, c, d = get_gpt_response(messages)

    # 创建新行的数据
    new_row = {
        "summary": i["gpt_summary_response"],
        "original_title": i["gpt_title_response"],
        "new_title": new_title,
    }
    # 将新行数据添加到列表
    rows.append(new_row)
    logger.info(f"summary: {i['gpt_summary_response']}")
    logger.warning(f"original_title: {i['gpt_title_response']}")
    logger.error(f"new_title: {new_title}")

# 一次性将列表转换成DataFrame
df = pd.DataFrame(rows, columns=["summary", "original_title", "new_title"])

# 显示DataFrame
print(df)

# 将DataFrame保存为CSV文件
# df.to_csv("test_summary_vs_title_Cog.csv", index=False, encoding="utf-8-sig")
