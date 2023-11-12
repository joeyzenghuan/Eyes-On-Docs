from logs import logger

import os

from azure.identity import DefaultAzureCredential  
from cosmosdbservice import CosmosConversationClient

# CosmosDB Integration Settings
AZURE_COSMOSDB_DATABASE = os.getenv("AZURE_COSMOSDB_DATABASE")
AZURE_COSMOSDB_ACCOUNT = os.getenv("AZURE_COSMOSDB_ACCOUNT")
AZURE_COSMOSDB_CONVERSATIONS_CONTAINER = os.getenv("AZURE_COSMOSDB_CONVERSATIONS_CONTAINER")
AZURE_COSMOSDB_ACCOUNT_KEY = os.getenv("AZURE_COSMOSDB_ACCOUNT_KEY")
save_commit_history_to_cosmosdb = False

print(AZURE_COSMOSDB_ACCOUNT_KEY)

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