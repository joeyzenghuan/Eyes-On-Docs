
import json
import os
import sys

from dotenv import load_dotenv
load_dotenv()


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
AZURE_COSMOSDB_CONVERSATIONS_CONTAINER = os.getenv("AZURE_COSMOSDB_CONVERSATIONS_CONTAINER")
AZURE_COSMOSDB_ACCOUNT_KEY = os.getenv("AZURE_COSMOSDB_ACCOUNT_KEY")
save_commit_history_to_cosmosdb = False

# print(AZURE_COSMOSDB_DATABASE, AZURE_COSMOSDB_ACCOUNT, AZURE_COSMOSDB_CONVERSATIONS_CONTAINER)
# print(AZURE_COSMOSDB_ACCOUNT_KEY)

# Initialize a CosmosDB client with AAD auth and containers
cosmos_conversation_client = None
if AZURE_COSMOSDB_DATABASE and AZURE_COSMOSDB_ACCOUNT and AZURE_COSMOSDB_CONVERSATIONS_CONTAINER:
    save_commit_history_to_cosmosdb = True
    try :
        cosmos_endpoint = f'https://{AZURE_COSMOSDB_ACCOUNT}.documents.azure.com:443/'

        if not AZURE_COSMOSDB_ACCOUNT_KEY:
            credential = DefaultAzureCredential()
        else:
            credential = AZURE_COSMOSDB_ACCOUNT_KEY

        cosmos_conversation_client = CosmosConversationClient(
            cosmosdb_endpoint=cosmos_endpoint, 
            credential=credential, 
            database_name=AZURE_COSMOSDB_DATABASE,
            container_name=AZURE_COSMOSDB_CONVERSATIONS_CONTAINER
        )
        print(cosmos_conversation_client)
    except Exception as e:
        logger.exception("Exception in CosmosDB initialization", e)
        save_commit_history_to_cosmosdb = False
        cosmos_conversation_client = None

with open('target_config.json', 'r') as f:
    targets = json.load(f)
    for d in targets:
        topic = d['topic_name']
        # topic = "abc"
        root_commits_url = d['root_commits_url']
        language = d['language']
        teams_webhook_url = d['teams_webhook_url']

        print(topic,  "---", language)

        lastest_commit_in_cosmosdb = cosmos_conversation_client.get_lastest_commit(topic, language, root_commits_url, sort_order = 'DESC')
        # print(lastest_commit_in_cosmosdb)
        if lastest_commit_in_cosmosdb:
            print(lastest_commit_in_cosmosdb['commit_time'])
            print(lastest_commit_in_cosmosdb['commit_url'])
        else:
            print("No commit history in CosmosDB")










