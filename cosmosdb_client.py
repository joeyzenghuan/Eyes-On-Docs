import os  
import datetime  
import time
from azure.identity import DefaultAzureCredential  
from cosmosdbservice import CosmosConversationClient  
from logs import logger  
from dotenv import load_dotenv
load_dotenv()

class CosmosDBHandler:  
    def __init__(self):  
        self.database = os.getenv("AZURE_COSMOSDB_DATABASE")  
        self.account = os.getenv("AZURE_COSMOSDB_ACCOUNT")  
        self.container = os.getenv("AZURE_COSMOSDB_CONVERSATIONS_CONTAINER")  
        self.account_key = os.getenv("AZURE_COSMOSDB_ACCOUNT_KEY")  
        

    def initialize_cosmos_client(self):  
        """初始化 CosmosDB 客戶端"""  
        try:  
            endpoint = f'https://{self.account}.documents.azure.com:443/'  
            if not self.account_key:
                credential = DefaultAzureCredential()
            else:
                credential = self.account_key
            client = CosmosConversationClient(  
                cosmosdb_endpoint=endpoint,   
                credential=credential,   
                database_name=self.database,  
                container_name=self.container  
            )  
            logger.info("Successfully initialized the CosmosDB client!")  
            self.save_commit_history_to_cosmosdb = True
            return client  
        except Exception as e:  
            logger.exception("An exception occurred during CosmosDB initialization", e)  
            self.save_commit_history_to_cosmosdb = False
            return None  
   
    def get_start_time(self, lastest_commit_in_cosmosdb):  
        """Get the starting point in time for fetching commits."""  
        lastest_commit_time_in_cosmosdb = None  
        try:
            if lastest_commit_in_cosmosdb:
                lastest_commit_time_in_cosmosdb = lastest_commit_in_cosmosdb['commit_time']

                lastest_commit_time_in_cosmosdb = lastest_commit_time_in_cosmosdb.strip()
                lastest_commit_time_in_cosmosdb = datetime.datetime.strptime(
                    lastest_commit_time_in_cosmosdb, "%Y-%m-%d %H:%M:%S"
                )
        except Exception as e:  
            logger.exception("Exception in getting lastest_commit_time_in_cosmosdb", e)  
  
        time_in_last_crawl_time_txt = self.read_time()  
  
        time_now = datetime.datetime.now()
        time_now_struct = time.mktime(time_now.timetuple())
        time_now_utc = datetime.datetime.utcfromtimestamp(time_now_struct)
  
        if lastest_commit_time_in_cosmosdb is None and time_in_last_crawl_time_txt is None:  
            self.write_time(time_now_utc)  
            logger.warning(f"No Commit in cosmosdb! Use current time as start time: {time_now_utc}")  
            return time_now  
        elif lastest_commit_time_in_cosmosdb == None and time_in_last_crawl_time_txt != None:
            logger.warning(f"No Commit in cosmosdb! Use last_crawl_time.txt as start time: {time_in_last_crawl_time_txt}")
            return time_in_last_crawl_time_txt  
        elif lastest_commit_time_in_cosmosdb != None and time_in_last_crawl_time_txt == None:
            logger.warning(f"Found Commits in cosmosdb! Use lastest_commit_time_in_cosmosdb as start time: {lastest_commit_time_in_cosmosdb}")
            return lastest_commit_time_in_cosmosdb  
        elif lastest_commit_time_in_cosmosdb != None and time_in_last_crawl_time_txt != None:
            if lastest_commit_time_in_cosmosdb > time_in_last_crawl_time_txt:
                logger.warning(f"lastest_commit_time_in_cosmosdb > time_in_last_crawl_time_txt! Use lastest_commit_time_in_cosmosdb as start time: {lastest_commit_time_in_cosmosdb}")
                return lastest_commit_time_in_cosmosdb
            else:
                logger.warning(f"lastest_commit_time_in_cosmosdb <= time_in_last_crawl_time_txt! Use time_in_last_crawl_time_txt as start time: {time_in_last_crawl_time_txt}. ")
                logger.warning("It may skip some commits.")
                return time_in_last_crawl_time_txt
        
    def write_time(self, update_time):
        try:
            with open('last_crawl_time.txt', 'w') as f:
                f.write(str(update_time))
            f.close()
            logger.warning(f"Update last_crawl_time.txt: {update_time}")
        except Exception as e:
            logger.exception("Exception in write_time", e)

    def read_time(self):
        try:
            with open('last_crawl_time.txt') as f:
                time_in_file_readline = f.readline().strip()
                time_in_file = datetime.datetime.strptime(
                    time_in_file_readline, "%Y-%m-%d %H:%M:%S"
                )
        except Exception as e:
            # logger.error(f"Error reading time from file: {e}")
            logger.exception("Exception in read_time", e)
            time_in_file = None
        return time_in_file
