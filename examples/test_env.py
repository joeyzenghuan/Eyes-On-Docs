import json
import os
import sys

from dotenv import load_dotenv
load_dotenv('C:\\GitRepo\\DocUpdateNotificationBot2\\DocUpdateNotificationBot\\.env')


AZURE_COSMOSDB_DATABASE = os.getenv("AZURE_COSMOSDB_DATABASE")
AZURE_COSMOSDB_ACCOUNT = os.getenv("AZURE_COSMOSDB_ACCOUNT")
AZURE_COSMOSDB_CONVERSATIONS_CONTAINER = os.getenv("AZURE_COSMOSDB_CONVERSATIONS_CONTAINER")

APP_TENANT_ID = os.getenv("APP_TENANT_ID")
APP_CLIENT_ID = os.getenv("APP_CLIENT_ID")
APP_CLIENT_SECRET = os.getenv("APP_CLIENT_SECRET")

#print all variables
print(AZURE_COSMOSDB_DATABASE)
print(AZURE_COSMOSDB_ACCOUNT)
print(AZURE_COSMOSDB_CONVERSATIONS_CONTAINER)
print(APP_TENANT_ID)
print(APP_CLIENT_ID)
print(APP_CLIENT_SECRET)

