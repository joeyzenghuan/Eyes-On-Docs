import os  
import datetime  
import time
from azure.identity import DefaultAzureCredential  
from cosmosdbservice import CosmosConversationClient  
from logs import logger  
  
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
            credential = self.account_key or DefaultAzureCredential()  
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
            lastest_commit_time_in_cosmosdb = datetime.datetime.strptime(  
                lastest_commit_in_cosmosdb['commit_time'], "%Y-%m-%d %H:%M:%S"  
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
            # logger.error(f"Error writing time: {e}")
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

            # # if file doesn't exist, create a file, and use current time as start time
            # local_time = datetime.datetime.now()
            # time_struct = time.mktime(local_time.timetuple())
            # utc_st = datetime.datetime.utcfromtimestamp(time_struct)
            # time_in_file = utc_st
            # self.write_time(time_in_file)
            # logger.warning(f"Use current time as start time, and update last_crawl_time: {time_in_file}")

        return time_in_file
  
    def save_commit_history(self, commit_history):  
        """將提交歷史記錄保存到 CosmosDB"""  
        if self.client and commit_history:  
            try:  
                if self.client.create_commit_history(commit_history):  
                    logger.exception("An exception occurred during CosmosDB initialization", e)  
                    return True  
                else:  
                    logger.error("Failed to save commit history to CosmosDB!")  
                    return False  
            except Exception as e:  
                logger.exception("An exception occurred while saving commit history to CosmosDB", e)  
                return False  
        return False  
  
 
if __name__ == "__main__":
    cosmos_db_handler = CosmosDBHandler()  
    commit_history_data = {  
        'commit_time': '2023-11-28 00:00:00',  
        'commit_url': 'https://github.com/example/repo/commit/abc123',  
        'gpt_title_response': 'Updated documentation for feature XYZ',  
        'gpt_summary_response': 'Feature XYZ documentation has been updated with the latest information.',  
        'topic': 'Documentation Update',  
        'root_commits_url': 'https://github.com/example/repo/commits',  
        'language': 'en',
        'who you are': "Nick Shieh >///<"  
    }  
    cosmos_db_handler.save_commit_history(commit_history_data)  
