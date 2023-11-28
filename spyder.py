import requests
import datetime
import os  
from dotenv import load_dotenv  
from logs import logger  
from commit_fetch import CommitFetcher  
from cosmosdb_client import CosmosDBHandler  
from call_gpt import CallGPT

load_dotenv()  
PERSONAL_TOKEN = os.getenv("PERSONAL_TOKEN")  
  
class Spyder(CommitFetcher, CallGPT):  
    def __init__(self, topic, root_commits_url, language, teams_webhook_url, system_prompt_dict):  
        self.topic = topic
        self.language = language
        self.root_commits_url = root_commits_url
        self.teams_webhook_url = teams_webhook_url
        self.system_prompt_dict = system_prompt_dict
        
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


    def process_commits(self, selected_commits):  
        for key in selected_commits:
            time_, url = key, selected_commits[key]
            try:
                input_dic, time_, summary, commit_url = self.get_change_from_each_url(time_, url)
            except Exception as e:
                logger.error(f"Error getting change from url: {url}, Exception: {e}")
                logger.exception("Exception in process_each_commit:", e)
                

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
                self.save_commit_history(time_, commit_url, gpt_title, gpt_summary, status)  
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

                            # self.post_teams_message(gpt_title[2:], time_, gpt_summary, commit_url)
                            print(gpt_title[2:]+"\n\n"+gpt_summary+"\n\n")
        # Update the start time in CosmosDB  
        self.commit_history.clear()
        self.cosmosDB.write_time(self.latest_time)  
  
    def generate_gpt_responses(self, commit_data, language, prompts):  
        gpt_summary = self.gpt_summary(commit_data, language, prompts["GPT_SUMMARY_PROMPT"])  
        gpt_title = self.gpt_title(gpt_summary, language, prompts["GPT_TITLE_PROMPT"])  
        status = self.determine_status(gpt_title)  
        return gpt_summary, gpt_title, status  
  
    def save_commit_history(self, commit_time, commit_url, gpt_title, gpt_summary, status):  
        commit_history = {  
            'commit_time': str(commit_time),  
            'commit_url': str(commit_url),  
            'gpt_title_response': str(gpt_title),  
            'gpt_summary_response': str(gpt_summary),  
            'status': status,  
            'topic': self.topic,  
            'root_commits_url': self.root_commits_url,  
            'language': self.language  
        }  
        if self.cosmosDB_client.create_commit_history(commit_history):  
            logger.info("Successfully created commit history in CosmosDB!")  
        else:  
            logger.error("Failed to create commit history in CosmosDB!")  
  
    def determine_status(self, gpt_title):  
        # Determine if the commit should be skipped or a notification sent  
        if gpt_title.startswith('0 '):  
            status = 'skip'  
            logger.info(f"Skipping this commit: {gpt_title}")  
        else:  
            status = 'post'  
            logger.info(f"GPT title (without first 2 chars): {gpt_title[2:]}")  
        return status  


    def post_teams_message(self, gpt_title_response, time, gpt_summary_response, commit_url):  # 向teams发送信息的函数
        try:
            jsonData = {  # 向teams 发送的message必须是json格式
                "@type": "MessageCard",
                "themeColor": "0076D7",
                "title": str(gpt_title_response),
                "text": str(time) + "\n\n" + str(gpt_summary_response),
                "potentialAction": [
                    {
                        "@type": "OpenUri",
                        "name": "Go to commit page",
                        "targets": [{"os": "default", "uri": commit_url}],
                    },
                ],
            }
            logger.debug(f"Teams Message jsonData: {jsonData}")

            response = requests.post(self.teams_webhook_url, json=jsonData)
            response.raise_for_status()
            logger.info(f"Post message to Teams successfully!")

            self.commit_history["teams_message_jsondata"] = jsonData
            self.commit_history["teams_message_webhook_url"] = self.teams_webhook_url
        except requests.exceptions.HTTPError as err:
            logger.error(f"Error occured while sending message to Teams: {err}")
            logger.exception("HTTPError in post_teams_message:", err)
        except Exception as err:
            logger.error(f"An error occured in post_teams_message: {err}")
            logger.exception("Unknown Exception in post_teams_message:", err)


    
    
    def push_weekly_summary(self):
        self.commit_history.clear()
        logger.warning(f"Push weekly summary report to teams")
        weekly_commit_list = self.cosmosDB_client.get_weekly_commit(self.topic, self.language, self.root_commits_url, sort_order = 'DESC')
        gpt_weekly_summary_response = self.get_weekly_summary(self.language, weekly_commit_list, self.system_prompt_dict["GPT_WEEKLY_SUMMARY_PROMPT"])
        today = datetime.date.today() 
  
        # 計算今天是週幾（週一為0，週日為6）  
        weekday = today.weekday()  
        
        # 計算上周一的日期  
        last_monday = today - datetime.timedelta(days=weekday+7)  
        
        # 計算上周日的日期  
        last_sunday = last_monday + datetime.timedelta(days=6)  
        try:
            
            # JSON for the adaptive card  
            if gpt_weekly_summary_response:
                # body = []
                # for i in range(len(gpt_weekly_summary_response), 2):
                #     if gpt_weekly_summary_response[i+1]:
                #         body.append({
                #                         "type": "TextBlock",
                #                         "text": gpt_weekly_summary_response[i],
                #                         "size": "medium",
                #                         "weight": "bolder",
                #                         "color": "good"
                #                     })
                #         body.append({
                #                         "type": "TextBlock",
                #                         "text": gpt_weekly_summary_response[i+1],
                #                         "wrap": True,
                #                         "color": "default"
                #                     })
                #         body.append({
                #                         "type": "TextBlock",
                #                         "text": "\n\n",
                #                         "wrap": True,
                #                         "color": "default"
                #                     })
                # adaptive_card_json = {  
                #     "type": "message",  
                #     "attachments": [  
                #         {  
                #             "contentType": "application/vnd.microsoft.card.adaptive",  
                #             "content": {  
                #                 "type": "AdaptiveCard",  
                #                 "body": body,  
                #                 "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",   
                #             }  
                #         }  
                #     ]  
                # }
                # adaptive_card_json_str = json.dumps(adaptive_card_json)  
                # response = requests.post(self.teams_webhook_url, json=adaptive_card_json)
                json_data = {  # 向teams 发送的message必须是json格式
                    "@type": "MessageCard",
                    "themeColor": "0076D7",
                    "title": f"[Weekly Summary] {last_monday} ~ {last_sunday}",
                    "text": str(gpt_weekly_summary_response),
                }
                logger.debug(f"Teams Message jsonData: {json_data}")

                # response = requests.post(self.teams_webhook_url, json=json_data)
                # response.raise_for_status()
                logger.info(f"Post message to Teams successfully!")
                self.commit_history["get_weekly_summary_status"] = "succeed"
                self.commit_history["teams_message_jsondata"] = json_data
            else:
                self.commit_history["get_weekly_summary_status"] = "failed"

            self.commit_history["teams_message_webhook_url"] = self.teams_webhook_url
            self.commit_history['commit_time'] = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            self.commit_history['topic'] = self.topic
            self.commit_history['root_commits_url'] = self.root_commits_url
            self.commit_history['language'] = self.language

            if self.cosmosDB.save_commit_history_to_cosmosdb:
                if self.cosmosDB_client.create_commit_history(self.commit_history):
                    logger.warning(f"Create commit history in CosmosDB successfully!")
                else:
                    logger.error(f"Create commit history in CosmosDB failed!")
            self.commit_history.clear()
        except requests.exceptions.HTTPError as err:
            logger.error(f"Error occured while sending message to Teams: {err}")
            logger.exception("HTTPError in post_teams_message:", err)
        except Exception as err:
            logger.error(f"An error occured in post_teams_message: {err}")
            logger.exception("Unknown Exception in post_teams_message:", err)