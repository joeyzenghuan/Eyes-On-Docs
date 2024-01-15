import requests
import datetime
import os  
from dotenv import load_dotenv  
from logs import logger  
from commit_fetch import CommitFetcher  
from cosmosdb_client import CosmosDBHandler  
from call_gpt import CallGPT
from teams_notifier import TeamsNotifier

load_dotenv()  
PERSONAL_TOKEN = os.getenv("PERSONAL_TOKEN")  
  
class Spyder(CommitFetcher, CallGPT, TeamsNotifier):  
    def __init__(self, topic, root_commits_url, language, teams_webhook_url, show_topic_in_title, system_prompt_dict, max_input_token):  
        self.topic = topic
        self.language = language
        self.root_commits_url = root_commits_url
        self.teams_webhook_url = teams_webhook_url
        self.system_prompt_dict = system_prompt_dict
        self.max_input_token = max_input_token
        self.show_topic_in_title = show_topic_in_title
        
        self.headers = {"Authorization": "token " + PERSONAL_TOKEN}
        # api_url = 'https://api.github.com/repos/MicrosoftDocs/azure-docs/commits'
        self.schedule = 7200
        self.cosmosDB = CosmosDBHandler()
        self.cosmosDB_client = self.cosmosDB.initialize_cosmos_client()
        lastest_commit_in_cosmosdb = self.cosmosDB_client.get_lastest_commit(self.topic, self.language, self.root_commits_url, sort_order = 'DESC')

        self.start_time = self.cosmosDB.get_start_time(lastest_commit_in_cosmosdb)
        all_commits = self.get_all_commits(self.root_commits_url, self.headers)
        self.latest_commits, self.latest_time = self.select_latest_commits(all_commits, self.start_time)  

        logger.info(f"Only get changes after the time point: {self.start_time}")
        self.commit_history = {}

    def determine_status(self, gpt_title):  
        # Determine if the commit should be skipped or a notification sent  
        if gpt_title.startswith('0 '):  
            status = 'skip'  
            logger.info(f"Skipping this commit: {gpt_title}")  
        else:  
            status = 'post'  
            logger.info(f"GPT title (without first 2 chars): {gpt_title[2:]}")  
        return status  

    def generate_gpt_responses(self, commit_data, language, prompts):  
        gpt_summary, gpt_summary_tokens, commit_patch_data = self.gpt_summary(commit_data, language, prompts["GPT_SUMMARY_PROMPT"])  
        # self.update_commit_history("gpt_summary_response", gpt_summary)
        self.update_commit_history("gpt_summary_tokens", gpt_summary_tokens)
        self.update_commit_history("commit_patch_data", commit_patch_data)
        gpt_title, gpt_title_tokens = self.gpt_title(gpt_summary, language, prompts["GPT_TITLE_PROMPT"])  
        # self.update_commit_history("gpt_title_response", gpt_title)
        self.update_commit_history("gpt_title_tokens", gpt_title_tokens)
        status = self.determine_status(gpt_title)  
        return gpt_summary, gpt_title, status  
    
    def generate_weekly_summary(self):
        self.commit_history.clear()
        logger.warning(f"Get last week summary from CosmosDB")
        weekly_commit_list = self.cosmosDB_client.get_weekly_commit(self.topic, self.language, self.root_commits_url, sort_order = 'DESC')
        if weekly_commit_list:
            logger.info(f"Find {len(weekly_commit_list)} last week summary in CosmosDB")
            gpt_weekly_summary_response, gpt_weekly_summary_tokens = self.get_weekly_summary(
                self.language, weekly_commit_list, self.system_prompt_dict["GPT_WEEKLY_SUMMARY_PROMPT"], self.max_input_token
                )
            try:
                if gpt_weekly_summary_response:
                    title = self.generate_weekly_title()
                    time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    logger.warning(f"Push weekly summary report to teams")
                    teams_message_jsondata, post_status, error_message = self.post_teams_message(title, time, gpt_weekly_summary_response, self.teams_webhook_url)
                    logger.debug(f"Teams Message jsonData: {teams_message_jsondata}")

                    self.save_commit_history(time, "", "", teams_message_jsondata, post_status, error_message)
                    self.update_commit_history("gpt_weekly_summary_tokens", gpt_weekly_summary_tokens)
                    self.update_commit_history("teams_message_webhook_url", self.teams_webhook_url)
                else:
                    logger.warning(f"No weekly summary report to teams")
                    self.save_commit_history(time, "", "", "", "failed", "No important update last week")
                self.upload_commit_history()

            except requests.exceptions.HTTPError as err:
                logger.error(f"Error occured while sending message to Teams: {err}")
                logger.exception("HTTPError in post_teams_message:", err)
            except Exception as err:
                logger.error(f"An error occured in post_teams_message: {err}")
                logger.exception("Unknown Exception in post_teams_message:", err)
        else:
            logger.warning(f"Last week summary in CosmosDB is empty")

    def generate_weekly_title(self):
        last_monday = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday() + 7)
        last_sunday = last_monday + datetime.timedelta(days=6)
        return f"[Weekly Summary] {last_monday} ~ {last_sunday}"

    def process_commits(self, selected_commits):  
        for key in selected_commits:
            time_, url = key, selected_commits[key]
            try:
                input_dic, time_, summary, commit_url = self.get_change_from_each_url(time_, url, self.max_input_token)
            except Exception as e:
                logger.error(f"Error getting change from url: {url}, Exception: {e}")
                logger.exception("Exception in process_each_commit:", e)
                
            teams_message_jsondata = None
            post_status = None
            error_message = None

            commit_patch_data = input_dic.get("commits")
            if commit_patch_data == "Error":
                logger.error(f"Error getting patch data from url: {commit_url}")
                gpt_summary = "Too many changes in one commit.🤦‍♂️ \n\nThe bot isn't smart enough to handle temporarily.😢 \n\nPlease check the update via commit page button.🤪"
                gpt_title = "Error in Getting Patch Data"
                status = "Error in Getting Patch Data"
            else:
                # Use GPT model to generate summary and title  
                gpt_summary, gpt_title, status = self.generate_gpt_responses(input_dic, self.language, self.system_prompt_dict)  
                # Save commit history to CosmosDB  
                  
                if gpt_summary == None:
                    gpt_summary = "Something went wrong when generating Summary😂.\n\n You can report the issue(\"...\" -> Copy link) to zehua@micrsoft.com, thanks."
                    gpt_title = "Error in getting Summary"
                    status = "Error in getting Summary"
                else:
                    if gpt_title == None:
                        gpt_title = "Error in getting Title"
                        status = "Error in getting Title"
                    else:
                        # check the first two characters of gpt_title, if it is '0 ', skip this commit
                        if status == "skip":
                            logger.error(f"Skip this commit: {gpt_title}")
                        else:
                            # lastest_commit_in_cosmosdb = cosmos_conversation_client.get_lastest_commit(self.topic, self.language, self.root_commits_url, sort_order = 'DESC')
                            # if self.get_similarity(input_dic, self.language, lastest_commit_in_cosmosdb, self.system_prompt_dict["GPT_SIMILARITL_PROMPT"]).split("\n")[1][0] == "1":
                            #     logger.error(f"Error detected content as similar to the previous entry, therefore skipping.")
                            # else:
                            logger.warning(f"GPT_Title without first 2 chars: {gpt_title[2:]}")
                            if self.show_topic_in_title:
                                time = self.topic + "\n\n" + str(time_)
                            else:
                                time = time_
                            teams_message_jsondata, post_status, error_message = self.post_teams_message(gpt_title[2:], time, gpt_summary, self.teams_webhook_url, commit_url)
                            # print(gpt_title[2:]+"\n\n"+gpt_summary+"\n\n")
            # Update the start time in CosmosDB 
            self.update_commit_history("gpt_summary_response", gpt_summary)
            self.update_commit_history("gpt_title_response", gpt_title)


            self.save_commit_history(time_, commit_url, status, teams_message_jsondata, post_status, error_message) 
            self.upload_commit_history()
            self.commit_history.clear()
  
    def save_commit_history(self, commit_time, commit_url=None, status=None, teams_message_jsondata=None, post_status=None, error_message=None):  
        self.update_commit_history("commit_time", str(commit_time)) 
        self.update_commit_history("commit_url", str(commit_url)) 
        self.update_commit_history("status", status) 
        self.update_commit_history("topic", self.topic) 
        self.update_commit_history("language", self.language) 
        self.update_commit_history("root_commits_url", self.root_commits_url) 
        self.update_commit_history("teams_message_webhook_url", self.teams_webhook_url)
        self.update_commit_history("teams_message_jsondata", teams_message_jsondata) 
        self.update_commit_history("post_status", post_status) 
        self.update_commit_history("error_message", error_message) 

    def update_commit_history(self, key, value):  
        """  
        更新提交历史记录。  
        :param key: 记录的键  
        :param value: 记录的值  
        """  
        self.commit_history[key] = value  

    def upload_commit_history(self):
        if self.cosmosDB_client.create_commit_history(self.commit_history):  
            logger.info("Successfully created commit history in CosmosDB!")  
        else:  
            logger.error("Failed to create commit history in CosmosDB!")  
        self.commit_history.clear()
    
    