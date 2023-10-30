import requests
import time
import datetime
import openai
import os
import json
from playwright.sync_api import Playwright, sync_playwright, expect
from bs4 import BeautifulSoup
import pymsteams
from PyQt5.QtWidgets import QApplication, QDialog
from spyder import Ui_Dialog
import sys
import threading
import time
from logs import logger


from dotenv import load_dotenv

load_dotenv()
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY")
# logger.debug(f"AZURE_OPENAI_KEY: {AZURE_OPENAI_KEY}")


class Spyder:
    def __init__(self):
        self.personal_token = "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"
        self.headers = {"Authorization": "token " + self.personal_token}
        # api_url = 'https://api.github.com/repos/MicrosoftDocs/azure-docs/commits'
        self.url2 = "https://github.com/MicrosoftDocs/azure-docs/commits/main/articles/ai-services/openai/"

        self.starttime = datetime.datetime.strptime(
            "2023-10-29T18:24:08Z", "%Y-%m-%dT%H:%M:%SZ"
        )
        logger.info(f"Only get changes after the time point: {self.starttime}")

        self.gitprefix = "https://github.com/MicrosoftDocs/azure-docs/blob/main/"
        self.mslearnprefix = "https://learn.microsoft.com/en-us/azure/"
        # local_time = datetime.datetime.now()
        # time_struct = time.mktime(local_time.timetuple())
        # utc_st = datetime.datetime.utcfromtimestamp(time_struct)
        # self.starttime = utc_st

    def get_commit_page(self):
        logger.info(f"Getting commit page:  {self.url2} ")

        response = requests.get(self.url2, headers=self.headers).text
        # logger.debug(f"Commit Page Raw Text: {response}")

        soup = BeautifulSoup(response, "html.parser")

        precise_time_list = []
        action_url = []
        action = soup.find_all("div", {"class": "TimelineItem-body"})
        for item in action:
            time_ = item.find_all("relative-time")
            for i in time_:
                a = i["datetime"]
                precise_time_list.append(
                    datetime.datetime.strptime(str(a), "%Y-%m-%dT%H:%M:%SZ")
                )

        action_u = soup.find_all(
            "a", {"class": "Link--primary text-bold js-navigation-open markdown-title"}
        )
        for item in action_u:
            if "https://github.com" + item["href"] not in action_url:
                action_url.append("https://github.com" + item["href"])

        page_dic = dict(zip(precise_time_list, action_url))
        return page_dic

    def select_latest(self):
        page_dic = self.get_commit_page()
        selected = {}
        for key in page_dic.keys():
            if key > self.starttime:
                selected[key] = page_dic[key]
        self.starttime = max(page_dic.keys())

        return selected

    def get_change(self, time, url):
        response = requests.get(url, headers=self.headers).text
        soup = BeautifulSoup(response, "html.parser")
        time_ = time
        if soup.find("div", {"class": "commit-desc"}):
            summary = soup.find("div", {"class": "commit-desc"}).pre.text
        else:
            summary = soup.find("div", class_="commit-title markdown-title").text

        commit_url = url
        url_list = []
        final_urls = []
        deleted_list = []
        added_list = []
        deleted = soup.find_all(
            "span",
            class_="blob-code-inner blob-code-marker js-code-nav-pass js-skip-tagsearch",
        )
        added = soup.find_all("span", {"data-code-marker": "+"})

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                extra_http_headers=self.headers,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76",
            )

            page = context.new_page()

            page.goto(url)
            # page.wait_for_load_state("networkidle")

            for i in page.locator(
                "//span[@class='Truncate']//a[@class='Link--primary Truncate-text']"
            ).all():
                url_list.append(i.inner_text())

            page.close()
            context.close()
            browser.close()
        for item in url_list:
            if "includes" in item:
                final_urls.append(self.gitprefix + item)
            else:
                item = item.replace("articles/", "").replace(".md", "")
                final_urls.append(self.mslearnprefix + item)

        for item in deleted:
            for i in item:
                deleted_list.append(i.text)
        for item in added:
            added_list.append(item.text)

        keys = ["added_list", "deleted_list", "urls"]
        values = [added_list, deleted_list, final_urls]
        result_dic = {}
        for i, key in enumerate(keys):
            result_dic[key] = values[i]
        
        logger.debug(f"Get Change result_dic: {result_dic}")

        return result_dic, time_, summary, commit_url

    def each_commit(self):
        selected = self.select_latest()
        for key in selected:
            time_, url = key, selected[key]
            input_dic, time_, summary, commit_url = self.get_change(time_, url)
            reply = self.gpt_summary(input_dic)
            self.postTeamsMessage(summary, time_, reply, commit_url)

    def postTeamsMessage(self, summary, time, text, commit_url):
        # WEBHOOK_URL = "https://uniofnottm.webhook.office.com/webhookb2/577208ca-2378-4222-a0d6-a5297dfec8a5@67bda7ee-fd80-41ef-ac91-358418290a1e/IncomingWebhook/49e2d97a9bfa452f82fcbf04bdc835b6/6701c303-f6a1-4998-bae1-b64f726f699e"
        WEBHOOK_URL = "https://microsoft.webhook.office.com/webhookb2/47e32e29-2419-41ba-bd3e-9a9e1c8c91eb@72f988bf-86f1-41af-91ab-2d7cd011db47/IncomingWebhook/c3279cbec95042eea542d56d98fab2eb/0e8f7dd6-18ac-459d-8def-328da20ecf7d"

        jsonData = {
            "@type": "MessageCard",
            "themeColor": "0076D7",
            "title": "[NEW ACTION]:" + "  " + str(summary) + " " + str(time),
            "text": text,
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

    def gpt_summary(self, input_dict):
        openai.api_type = "azure"
        openai.api_base = "https://ryanopenaicandaeast.openai.azure.com/"
        openai.api_version = "2023-07-01-preview"
        # openai.api_key = "b0df4f028e7c4ae49473a01a80aad1ef"
        openai.api_key = AZURE_OPENAI_KEY

        messages = [
            {
                "role": "system",
                "content": """you will get a dict style input ,*You need to make a summary of the deleted operations and the added operations*
                The dictionary has a total of 2 keys  added_list, deleted_list,
                added_list corresponding value is the content added by the user,Deletions and additions occur in added_list and 
                deleted_list corresponding positions, 
                and you should reflect the corresponding relationship when answering, deleted_
                The value corresponding to the list is the content deleted by the user,urls includes the links to each changed file.
                Dont't include meaningless punctuation in your reply.
                for example'[]''-','+' ,**Use bullets to make the answer clear and unambiguous** 
                [Deleted Action]:{use bullets to explain} , 
                [Added Action]:{use bullets to explain},
                URLS:{Each line displays a URL}
                """,
            },
            {"role": "user", "content": str(input_dict)},
        ]
        response = openai.ChatCompletion.create(
            engine="gpt432k",  # engine = "deployment_name".
            messages=messages,
        )
        gpt_response = response["choices"][0]["message"]["content"]

        logger.info(f"GPT Request body: {messages}")
        logger.info(f"GPT Response:  {gpt_response}")

        return gpt_response


class MainDialog(QDialog):
    def __init__(self, parent=None):
        super(QDialog, self).__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.schedule = 3600
        self.ui.pushButton.clicked.connect(self.run)
        self.ui.pushButton_2.clicked.connect(self.stop)

    def run(self):
        t = threading.Thread(target=self.on, name="t")
        t.start()

    def on(self):
        self.flag = 1
        self.ui.label_2.setText("Running...")
        while True:
            if self.flag == 1:
                git_spyder = Spyder()
                git_spyder.each_commit()
                self.ui.label_4.setText(str(git_spyder.starttime))
                time.sleep(self.schedule)
            else:
                break

    def stop(self):
        self.flag = 0
        self.ui.label_2.setText("Stop...")


if __name__ == "__main__":
    myapp = QApplication(sys.argv)
    myDlg = MainDialog()
    myDlg.show()
    sys.exit(myapp.exec_())
