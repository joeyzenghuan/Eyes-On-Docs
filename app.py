import requests
import time
import datetime
import openai
import os
import json
# from playwright.sync_api import Playwright, sync_playwright, expect
from bs4 import BeautifulSoup
# import pymsteams
# from PyQt5.QtWidgets import QApplication, QDialog
# from spyder import Ui_Dialog
# import sys
# import threading
import time

from logs import logger
from gpt_reply import *

from dotenv import load_dotenv

load_dotenv()

# openai.api_key = os.getenv("AZURE_OPENAI_KEY")
# openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
# # logger.debug(f"AZURE_OPENAI_KEY: {AZURE_OPENAI_KEY}")
# openai.api_type = "azure"
# openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
# deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# ROOT_COMMITS_URL = os.getenv("ROOT_COMMITS_URL")
# LANGUAGE = os.getenv("LANGUAGE")

import toml
with open('prompts.toml', 'r') as f:
    data = toml.load(f)

# gpt_summary_prompt = data['gpt_summary_prompt_v1']['prompt']
# gpt_title_prompt = data['gpt_title_prompt_v1']['prompt']

gpt_summary_prompt = data['gpt_summary_prompt_v2']['prompt']
gpt_title_prompt = data['gpt_title_prompt_v2']['prompt']


from azure.identity import DefaultAzureCredential  
from cosmosdbservice import CosmosConversationClient

# CosmosDB Integration Settings
AZURE_COSMOSDB_DATABASE = os.getenv("AZURE_COSMOSDB_DATABASE")
AZURE_COSMOSDB_ACCOUNT = os.getenv("AZURE_COSMOSDB_ACCOUNT")
AZURE_COSMOSDB_CONVERSATIONS_CONTAINER = os.getenv("AZURE_COSMOSDB_CONVERSATIONS_CONTAINER")
AZURE_COSMOSDB_ACCOUNT_KEY = os.getenv("AZURE_COSMOSDB_ACCOUNT_KEY")
save_commit_history_to_cosmosdb = False

# Initialize a CosmosDB client with AAD auth and containers
cosmos_conversation_client = None
if AZURE_COSMOSDB_DATABASE and AZURE_COSMOSDB_ACCOUNT and AZURE_COSMOSDB_CONVERSATIONS_CONTAINER:
    
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

        save_commit_history_to_cosmosdb = True
        logger.info(f"Initialize CosmosDB client successfully!")

    except Exception as e:
        logger.exception("Exception in CosmosDB initialization", e)
        save_commit_history_to_cosmosdb = False
        cosmos_conversation_client = None


class Spyder:
    def __init__(self, topic, root_commits_url, language, teams_webhook_url):
        self.personal_token = os.getenv("PERSONAL_TOKEN")
        # print(self.personal_token)
        self.headers = {"Authorization": "token " + self.personal_token}

        # api_url = 'https://api.github.com/repos/MicrosoftDocs/azure-docs/commits'
        self.schedule = 7200

        lastest_commit_time_in_cosmosdb = None
        if save_commit_history_to_cosmosdb:
            try:
                lastest_commit_in_cosmosdb = cosmos_conversation_client.get_lastest_commit(topic, language, root_commits_url, sort_order = 'DESC')
                # print(lastest_commit_in_cosmosdb)

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

        if lastest_commit_time_in_cosmosdb == None and time_in_last_crawl_time_txt == None:
            self.write_time(time_now_utc)
            logger.warning(f"No Commit in cosmosdb! Use current time as start time, and create last_crawl_time.txt: {time_now_utc}")
            self.starttime = time_now_utc
        elif lastest_commit_time_in_cosmosdb == None and time_in_last_crawl_time_txt != None:
            self.starttime = time_in_last_crawl_time_txt
            logger.warning(f"No Commit in cosmosdb! Use last_crawl_time.txt as start time: {self.starttime}")
        elif lastest_commit_time_in_cosmosdb != None and time_in_last_crawl_time_txt == None:
            self.starttime = lastest_commit_time_in_cosmosdb
            logger.warning(f"Found Commits in cosmosdb! Use lastest_commit_time_in_cosmosdb as start time: {self.starttime}")
            # self.write_time(lastest_commit_time_in_cosmosdb)
            # logger.warning(f"Create last_crawl_time.txt: {lastest_commit_time_in_cosmosdb}")
        elif lastest_commit_time_in_cosmosdb != None and time_in_last_crawl_time_txt != None:
            if lastest_commit_time_in_cosmosdb > time_in_last_crawl_time_txt:
                self.starttime = lastest_commit_time_in_cosmosdb
                logger.warning(f"lastest_commit_time_in_cosmosdb > time_in_last_crawl_time_txt! Use lastest_commit_time_in_cosmosdb as start time: {self.starttime}")
            else:
                self.starttime = time_in_last_crawl_time_txt
                logger.warning(f"lastest_commit_time_in_cosmosdb <= time_in_last_crawl_time_txt! Use time_in_last_crawl_time_txt as start time: {self.starttime}. ")
                logger.warning("It may skip some commits.")

        
        # *****从当前时间开始执行爬虫，只爬取比当前时间新的commit操作*****
        # local_time = datetime.datetime.now()
        # time_struct = time.mktime(local_time.timetuple())
        # utc_st = datetime.datetime.utcfromtimestamp(time_struct)
        # self.starttime = utc_st

        logger.info(f"Only get changes after the time point: {self.starttime}")

        # 爬虫起始网页，从openai的commits中开始爬取操作
        # self.root_commits_url = "https://github.com/MicrosoftDocs/azure-docs/commits/main/articles/ai-services/openai/"  
        self.root_commits_url = root_commits_url
        self.topic = topic
        self.language = language
        self.teams_webhook_url = teams_webhook_url
        
        # self.gitprefix = "https://github.com/MicrosoftDocs/azure-docs/blob/main/"
        # self.mslearnprefix = "https://learn.microsoft.com/en-us/azure/"

        #记录每次爬取的commit的时间，url，gpt生成的标题和总结等信息
        self.commit_history = {}


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
    
    # 获取所有根路径（openai）下的所有commmits操作，以及他们的时间
    def get_all_commits(self):  
        
        logger.info(f"Commit Root page:  {self.root_commits_url} ")

        response = requests.get(self.root_commits_url, headers=self.headers).text
        # logger.debug(f"Commit Page Raw Text: {response}")

        soup = BeautifulSoup(response, "html.parser")

        precise_time_list = []
        commits_url_list = []
        commits_url_html = []
        # 每天的所有commits集合 <div class="TimelineItem-body">
        commits_per_day = soup.find_all("div", {"class": "TimelineItem-body"})

        for item in commits_per_day:

            # <relative-time datetime="2023-10-31T17:37:03Z" class="no-wrap" title="Nov 1, 2023, 1:37 AM GMT+8">Nov 1, 2023</relative-time>
            time_ = item.find_all("relative-time")
            for i in time_:
                a = i["datetime"]
                precise_time_list.append(  # 获取这一天commits的所有时间
                    datetime.datetime.strptime(str(a), "%Y-%m-%dT%H:%M:%SZ")
                )
            
            for i in item.find_all(  # 获取当前div中的第一条url
                "div", {"class": "flex-auto min-width-0 js-details-container Details"}):
                    commits_url_html.append(i.find('a','Link--primary text-bold js-navigation-open markdown-title').get('href'))

        for item in commits_url_html:
            commits_url_list.append("https://github.com" + item)

        commits_dic_time_url = dict(
            zip(precise_time_list, commits_url_list)
        )  # 将时间和url打包成字典，字典的键是时间，字典的值是url
        return commits_dic_time_url

    # 将每个时间与当前记录的最新时间对比，选出比当前最新时间还要大的时间，同时更新最新时间。
    def select_latest_commits(self,commits_dic_time_url):  
        # commits_dic_time_url = self.get_all_commits()

        selected_commits = {}

        for key in commits_dic_time_url.keys():
            if key > self.starttime:
                selected_commits[key] = commits_dic_time_url[key]

        # 按时间排序
        selected_commits = dict(sorted(selected_commits.items(), key=lambda x: x[0]))
        # self.write_time(str(max(commits_dic_time_url.keys())))

        selected_commits_length = len(selected_commits)
        logger.warning(f"++++++++++++++++++++++++ {selected_commits_length} selected commits: {selected_commits}")

        if selected_commits_length > 0:
            latest_crawl_time = str(max(selected_commits.keys()))
            logger.warning(f"Max new commits time: {latest_crawl_time}")
        else:
            latest_crawl_time = self.starttime
            # logger.warning(f"No new commits, keep the latest crawl time: {latest_crawl_time}")
            logger.warning(f"No new commits")

        return selected_commits, latest_crawl_time  # 返回筛选完的时间以及对应url
        # return selected_commits  # 返回筛选完的时间以及对应url

    # 输入事件时间和url 并获取这个url中包含的所有文件url，时间，总结，删除和增加的操作并返回
    def get_change_from_each_url(
        self, time, commit_url
    ): 
        logger.warning(f"Getting changes from url: {commit_url}")

        # response = requests.get(commit_url, headers=self.headers).text

        try:
            response = response = requests.get(commit_url, headers=self.headers)
            response.raise_for_status()
            response_raw_text = response.text
        except Exception as e:
            logger.error("Exception in get_change_from_each_url:", e)
            logger.exception("Exception in get_change_from_each_url:", e)

        soup = BeautifulSoup(response_raw_text, "html.parser")
        time_ = time

        commit_title = soup.find("div", class_="commit-title markdown-title").text if soup.find("div", class_="commit-title markdown-title") else ""
        commit_desc = soup.find("div", {"class": "commit-desc"}).pre.text if soup.find("div", {"class": "commit-desc"}) else ""

        commit_title_and_desc = (
            f"commit_title: {commit_title}, commit_desc: {commit_desc}"
        )
        logger.info(f"commit_title_and_desc: {commit_title_and_desc}")

      
        url_list = []
        final_urls = []
        patch_url = commit_url + ".patch"

        logger.info(f"Getting patch data from url: {patch_url}")
        # response_patch = requests.get(patch_url, stream=True, headers=self.headers).text
        # response_raw_text = response_patch

        try:
            response = requests.get(patch_url, stream=True, headers=self.headers)
            response.raise_for_status()
            response_raw_text = response.text
            # print(response_raw_text)
        except requests.exceptions.HTTPError as errh:
            logger.exception("HTTP Error:", errh)
            response_raw_text = "Error"
        except requests.exceptions.ConnectionError as errc:
            logger.exception("Error Connecting:", errc)
            response_raw_text = "Error"
        except requests.exceptions.Timeout as errt:
            logger.exception("Timeout Error:", errt)
            response_raw_text = "Error"
        except requests.exceptions.RequestException as err:
            logger.exception("Something went wrong:", err)
            response_raw_text = "Error"
        except Exception as e:
            logger.exception("Unknown Exception:", e)
            response_raw_text = "Error"



        logger.warning(f"Patch data length: {len(response_raw_text)}")
        if len(response_raw_text) >= 30000:
            logger.warning(f"Patch data is too long, only get the first 30000 characters")
            patch_data = response_raw_text[:30000]
        else:
            patch_data = response_raw_text


        keys = ["commits", "urls"]
        values = [patch_data, final_urls]
        result_dic = {}
        for i, key in enumerate(keys):
            result_dic[key] = values[i]

        logger.debug(
            f"Get Change result_dic: {result_dic}"
        )  # 时间，commit的url，总结 都按照结构化返回，增加和删除的操作内容以及包含的所有被修改文件的url 都打包成字典后续传给gpt4处理。

        return result_dic, time_, commit_title_and_desc, commit_url

    def process_each_commit(self,selected_commits):  # 循环，对每一个筛选完的，确认更新的链接点击进去并执行上面的函数对内容进行爬取
        # selected_commits = self.select_latest_commits()

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
                gpt_summary_response = "Too many changes in one commit.🤦‍♂️ \n\nThe bot isn't smart enough to handle temporarily.😢 \n\nPlease check the update via commit page button.🤪"
                # gpt_title_response = "[!!]Need to check the update in commit page manually.😂"
                gpt_title_response = "Error in Getting Patch Data"
            else:
                gpt_summary_response = self.gpt_summary(input_dic)
                if gpt_summary_response == None:
                    gpt_summary_response = "Something went wrong when generating Summary😂.\n\n You can report the issue(\"...\" -> Copy link) to zehua@micrsoft.com, thanks."
                    # gpt_title_response = "[!!]Need to check the update in commit page manually.😂"
                    gpt_title_response = "Error in getting Summary"
                else:
                    gpt_title_response = self.gpt_title(gpt_summary_response)
                    if gpt_title_response == None:
                        # gpt_title_response = "Something went wrong when generating Title😂.\n\n You can report the issue(\"...\" -> Copy link) to zehua@micrsoft.com, thanks."
                        gpt_title_response = "Error in getting Title"
                    else:
                        self.post_teams_message(gpt_title_response, time_, gpt_summary_response, commit_url)
                

            # self.post_teams_message(gpt_title_response, time_, gpt_summary_response, commit_url)

            self.commit_history['commit_time'] = str(time_)
            self.commit_history['commit_url'] = str(commit_url)
            self.commit_history['gpt_title_response'] = str(gpt_title_response)
            self.commit_history['gpt_summary_response'] = str(gpt_summary_response)

            self.commit_history['topic'] = self.topic
            self.commit_history['root_commits_url'] = self.root_commits_url
            self.commit_history['language'] = self.language

            if save_commit_history_to_cosmosdb:
                if cosmos_conversation_client.create_commit_history(self.commit_history):
                    logger.warning(f"Create commit history in CosmosDB successfully!")
                else:
                    logger.error(f"Create commit history in CosmosDB failed!")

            self.commit_history.clear()

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


    # 调用GPT4 总结删除和增加的内容
    def gpt_summary(self, input_dict):  
        commit_patch_data = input_dict.get("commits")

        system_message = f"{gpt_summary_prompt} Reply in {self.language}."

        messages = [
            {
                "role": "system",
                "content": system_message,
            },
            # {"role": "user", "content": str(input_dict)},
            {"role": "user", "content": f"Here are the commit patch data. ###{commit_patch_data} ### Reply in {self.language}"},
        ]

        logger.info(f"GPT_Summary Request body: {messages}")

        gpt_summary_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages)
        
        logger.warning(f"GPT_Summary Response:\n  {gpt_summary_response}")
        logger.info(f"GPT_Summary Prompt tokens:  {prompt_tokens}")
        logger.info(f"GPT_Summary Completion tokens:  {completion_tokens}")
        logger.info(f"GPT_Summary Total tokens:  {total_tokens}")

        gpt_summary_response = gpt_summary_response\
        .replace("/articles/", "https://learn.microsoft.com/en-us/azure/") \
        .replace("articles/", "https://learn.microsoft.com/en-us/azure/") \
        .replace(".md", "") \
        .replace("/windows-driver-docs-pr/", "https://learn.microsoft.com/en-us/windows-hardware/drivers/") \
        .replace("windows-driver-docs-pr/", "https://learn.microsoft.com/en-us/windows-hardware/drivers/") \
        .replace("/docs/", "https://learn.microsoft.com/en-us/fabric/") \
        .replace("docs/", "https://learn.microsoft.com/en-us/fabric/")

        logger.warning(f"Correct Links in GPT_Summary Response:\n  {gpt_summary_response}")

        self.commit_history["gpt_summary_response"] = gpt_summary_response
        self.commit_history["gpt_summary_prompt_tokens"] = prompt_tokens
        self.commit_history["gpt_summary_completion_tokens"] = completion_tokens
        self.commit_history["gpt_summary_total_tokens"] = total_tokens

        return gpt_summary_response

    def gpt_title(self, input_):  # 调用GPT生成标题

        # system_prompt ="Give me a Chinese title to summarize the input. Don't mention user's name in the title.",
        system_prompt = f"{gpt_title_prompt} Reply in {self.language}."

#         system_prompt = """
# User will provide a summary of the Microsoft Document update change history. Please generate a short title based on user input.
# If the content is about GPT model update, please add [!!Model Update!!] at the beginning of the title.
# If the content is about code change, please add [!!Code Change!!] at the beginning of the title.
# Don't mention user's name in the title.
# Reply in Chinese."""
        messages = [
            {
                "role": "system",
                "content": str(system_prompt),
            },
            {"role": "user", "content": str(input_)},
        ]

        logger.info(f"GPT_Title Request body: {messages}")

        # response = openai.ChatCompletion.create(
        #     engine=deployment_name,  # engine = "deployment_name".
        #     messages=messages,
        #     temperature=0,
        # )

        # response = get_gpt_response(messages)

        gpt_title_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages)

        # gpt_title_response = response["choices"][0]["message"]["content"]
        # prompt_tokens = response["usage"]["prompt_tokens"]
        # completion_tokens = response["usage"]["completion_tokens"]
        # total_tokens = response["usage"]["total_tokens"]

        logger.info(f"GPT_Title Prompt tokens:  {prompt_tokens}")
        logger.info(f"GPT_Title Completion tokens:  {completion_tokens}")
        logger.info(f"GPT_Title Total tokens:  {total_tokens}")

        logger.warning(f"GPT_Title Response:\n {gpt_title_response}")

        self.commit_history["gpt_title_response"] = gpt_title_response
        self.commit_history["gpt_title_prompt_tokens"] = prompt_tokens
        self.commit_history["gpt_title_completion_tokens"] = completion_tokens
        self.commit_history["gpt_title_total_tokens"] = total_tokens

        return gpt_title_response

        
if __name__ == "__main__": 
    while True:
        try:
            with open('target_config.json', 'r') as f:
                targets = json.load(f)
                for d in targets:
                    topic = d['topic_name']
                    root_commits_url = d['root_commits_url']
                    language = d['language']
                    teams_webhook_url = d['teams_webhook_url']

                    logger.warning(f"========================= Start to process topic: {topic} =========================")
                    logger.info(f"Root commits url: {root_commits_url}")
                    logger.info(f"Language: {language}")
                    logger.info(f"Teams webhook url: {teams_webhook_url}")

                    git_spyder = Spyder(topic, root_commits_url, language, teams_webhook_url)
                    all_commits_from_root_commits_url = git_spyder.get_all_commits()
                    selected_commits, latest_crawl_time = git_spyder.select_latest_commits(all_commits_from_root_commits_url)
                    # selected_commits = git_spyder.select_latest_commits(all_commits_from_root_commits_url)

                    git_spyder.process_each_commit(selected_commits)
                    logger.warning(f"Finish processing topic: {topic}")


                    # git_spyder.write_time(latest_crawl_time)

                    # if latest_crawl_time != git_spyder.starttime:
                    #     git_spyder.write_time(latest_crawl_time)
                    
                    # git_spyder.get_change_from_each_url("12345", "https://github.com/MicrosoftDocs/azure-docs/commit/a2332df378bcd1f30acbed9dad066c70f9410bb8")

            # git_spyder.write_time(last_crawl_time)

            logger.warning(f"Waiting for {git_spyder.schedule} seconds")
            time.sleep(git_spyder.schedule)
           
        except Exception as e:
            logger.exception("Unexpected expection:", e)

            

