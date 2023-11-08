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


from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("AZURE_OPENAI_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
# logger.debug(f"AZURE_OPENAI_KEY: {AZURE_OPENAI_KEY}")
openai.api_type = "azure"
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")

root_commits_url = os.getenv("ROOT_COMMITS_URL")
language = os.getenv("LANGUAGE")

import toml
with open('prompts.toml', 'r') as f:
    data = toml.load(f)

gpt_summary_prompt = data['gpt_summary_prompt_v1']['prompt']
gpt_title_prompt = data['gpt_title_prompt_v1']['prompt']

print(f"gpt_summary_prompt: {gpt_summary_prompt}")
print(f"gpt_title_prompt: {gpt_title_prompt}")

class Spyder:
    def __init__(self):
        self.personal_token = os.getenv("PERSONAL_TOKEN")
        print(self.personal_token)
        self.headers = {"Authorization": "token " + self.personal_token}
        # api_url = 'https://api.github.com/repos/MicrosoftDocs/azure-docs/commits'
        self.schedule = 3600

        self.starttime = self.read_time()
        logger.info(f"Only get changes after the time point: {self.starttime}")

        # 爬虫起始网页，从openai的commits中开始爬取操作
        # self.main_url = "https://github.com/MicrosoftDocs/azure-docs/commits/main/articles/ai-services/openai/"  
        self.main_url = root_commits_url
        
        # self.gitprefix = "https://github.com/MicrosoftDocs/azure-docs/blob/main/"
        # self.mslearnprefix = "https://learn.microsoft.com/en-us/azure/"

        # *****从当前时间开始执行爬虫，只爬取比当前时间新的commit操作*****
        # local_time = datetime.datetime.now()
        # time_struct = time.mktime(local_time.timetuple())
        # utc_st = datetime.datetime.utcfromtimestamp(time_struct)
        # self.starttime = utc_st
        # *****正式使用请取消注释*****


    def write_time(self,update_time):
        with open('last_crawl_time.txt','w') as f:
            f.write(str(update_time))
        f.close()
        logger.warning(f"Update time config file: {update_time}")

    def read_time(self):
        try:
            with open('last_crawl_time.txt') as f:
                time_in_file = datetime.datetime.strptime(
                    f.readline(), "%Y-%m-%d %H:%M:%S"
                )
        except Exception as e:
            logger.error(f"Error reading time from file: {e}")
            # time_in_file = datetime.datetime.now()

            local_time = datetime.datetime.now()
            time_struct = time.mktime(local_time.timetuple())
            utc_st = datetime.datetime.utcfromtimestamp(time_struct)
            time_in_file = utc_st
            self.write_time(time_in_file)
            logger.warning(f"Use current time as start time, and update last_crawl_time: {time_in_file}")
        return time_in_file
    
    # 获取所有根路径（openai）下的所有commmits操作，以及他们的时间
    def get_all_commits(self):  
        logger.info(f"Commit Root page:  {self.main_url} ")

        response = requests.get(self.main_url, headers=self.headers).text
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
        logger.info(f"{selected_commits_length} selected commits: {selected_commits}")

        if selected_commits_length > 0:
            latest_crawl_time = str(max(selected_commits.keys()))
            logger.warning(f"Max new commits time: {latest_crawl_time}")
        else:
            latest_crawl_time = self.starttime
            logger.warning(f"No new commits, keep the latest crawl time: {latest_crawl_time}")

        return selected_commits, latest_crawl_time  # 返回筛选完的时间以及对应url

    # 输入事件时间和url 并获取这个url中包含的所有文件url，时间，总结，删除和增加的操作并返回
    def get_change_from_each_url(
        self, time, commit_url
    ): 
        logger.info(f"Getting changes from url: {commit_url}")

        response = requests.get(commit_url, headers=self.headers).text
        soup = BeautifulSoup(response, "html.parser")
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
        response_patch = requests.get(patch_url, stream=True, headers=self.headers).text
        temp_data = response_patch
        logger.warning(f"Patch data length: {len(temp_data)}")
        if len(temp_data) >= 30000:
            logger.warning(f"Patch data is too long, only get the first 30000 characters")
            patch_data = temp_data[:30000]
        else:
            patch_data = temp_data


        #（暂不启用）
        # playwright 框架等待网页加载并爬取，这样可以避免爬取内容不全的情况

        # with sync_playwright() as p:  
        #     browser = p.chromium.launch(headless=True)
        #     context = browser.new_context(
        #         extra_http_headers=self.headers,
        #         user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76",
        #     )

        #     page = context.new_page()

        #     page.goto(commit_url)
        #     page.wait_for_load_state()  # 等待网页加载完成

        #     for i in page.locator(
        #         "//span[@class='Truncate']//a[@class='Link--primary Truncate-text']"  # 使用x-path 获取被修改文件的路径
        #     ).all():
        #         logger.info(f"Getting changed file url: {i.inner_text()}")
        #         url_list.append(i.inner_text())

        #     page.close()
        #     context.close()
        #     browser.close()

        # for  item in url_list:  # 将获取的url和前缀进行拼接，带有includes的路径只能跳转到对应的github页面，无法跳转到microsoft.learn的页面
        #     if "includes" in item:
        #         final_urls.append(self.gitprefix + item)  # 筛选不同的url按照不同规则进行拼接
        #         logger.info(f"Final url(includes detected): {self.gitprefix + item}")
        #     else:
        #         temp_item = item.replace("articles/", "").replace(".md", "")
        #         final_urls.append(self.mslearnprefix + temp_item)
        #         logger.info(f"Final url: {self.mslearnprefix + temp_item}")

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
            input_dic, time_, summary, commit_url = self.get_change_from_each_url(
                time_, url
            )
            gpt_summary_response = self.gpt_summary(input_dic)
            gpt_title_response = self.gpt_title(gpt_summary_response)

            self.post_teams_message(gpt_title_response, time_, gpt_summary_response, commit_url)

    def post_teams_message(self, gpt_title_response, time, gpt_summary_response, commit_url):  # 向teams发送信息的函数
        WEBHOOK_URL = os.getenv("WEBHOOK_URL")

        jsonData = {  # 向teams 发送的message必须是json格式
            "@type": "MessageCard",
            "themeColor": "0076D7",
            "title": str(gpt_title_response),
            "text": str(time) + "\n\n" + gpt_summary_response,
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "Go to commit page",
                    "targets": [{"os": "default", "uri": commit_url}],
                },
            ],
        }
        logger.debug(f"Teams Message jsonData: {jsonData}")
        requests.post(WEBHOOK_URL, json=jsonData)

    # 调用GPT4 总结删除和增加的内容
    def gpt_summary(self, input_dict):  
        commit_patch_data = input_dict.get("commits")

        system_message = f"{gpt_summary_prompt} Reply in {language}."

        messages = [
            {
                "role": "system",
                "content": system_message,
            },
            # {"role": "user", "content": str(input_dict)},
            {"role": "user", "content": f"Here are the commit patch data. ###{commit_patch_data} ###"},
        ]

        logger.info(f"GPT_Summary Request body: {messages}")
        response = openai.ChatCompletion.create(
            engine=deployment_name,  # engine = "deployment_name".
            messages=messages,
            temperature=0,
        )
        gpt_summary_response_ = response["choices"][0]["message"]["content"]
        prompt_tokens = response["usage"]["prompt_tokens"]
        completion_tokens = response["usage"]["completion_tokens"]
        total_tokens = response["usage"]["total_tokens"]
        
        logger.info(f"GPT_Summary Response:  {gpt_summary_response_}")
        logger.warning(f"GPT_Summary Prompt tokens:  {prompt_tokens}")
        logger.warning(f"GPT_Summary Completion tokens:  {completion_tokens}")
        logger.warning(f"GPT_Summary Total tokens:  {total_tokens}")

        return gpt_summary_response_

    def gpt_title(self, input_):  # 调用GPT生成标题

        # system_prompt ="Give me a Chinese title to summarize the input. Don't mention user's name in the title.",
        system_prompt = f"{gpt_title_prompt} Reply in {language}."

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

        response = openai.ChatCompletion.create(
            engine=deployment_name,  # engine = "deployment_name".
            messages=messages,
            temperature=0,
        )
        gpt_title_response = response["choices"][0]["message"]["content"]
        prompt_tokens = response["usage"]["prompt_tokens"]
        completion_tokens = response["usage"]["completion_tokens"]
        total_tokens = response["usage"]["total_tokens"]

        logger.warning(f"GPT_Title Prompt tokens:  {prompt_tokens}")
        logger.warning(f"GPT_Title Completion tokens:  {completion_tokens}")
        logger.warning(f"GPT_Title Total tokens:  {total_tokens}")

        logger.info(f"GPT_Title Response:  {gpt_title_response}")

        return gpt_title_response

        
if __name__ == "__main__": 
    while True:
        git_spyder = Spyder()
        all_commits_from_main_url = git_spyder.get_all_commits()
        selected_commits, latest_crawl_time = git_spyder.select_latest_commits(all_commits_from_main_url)
        git_spyder.process_each_commit(selected_commits)

        if latest_crawl_time != git_spyder.starttime:
            git_spyder.write_time(latest_crawl_time)
        
        # git_spyder.get_change_from_each_url("12345", "https://github.com/MicrosoftDocs/azure-docs/commit/a2332df378bcd1f30acbed9dad066c70f9410bb8")

        logger.warning(f"Waiting for {git_spyder.schedule} seconds")
        time.sleep(git_spyder.schedule)
