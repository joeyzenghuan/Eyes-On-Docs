import json  
import time  
import datetime  
from dotenv import load_dotenv  
import toml  
  
from logs import logger  
from gpt_reply import *  
from spyder import *  
  
load_dotenv()  
  
def load_system_prompts():  
    """
    讀取prompts.toml中的system prompt，若要使用其他版本的prompt請在此處選擇v1、v2、v3....
    更改prompt請依照順序v1->v2->v3，請勿直接更改現有版本！！！
    """
    with open('prompts.toml', 'r') as f:  
        data = toml.load(f)  
    return {  
        "GPT_SUMMARY_PROMPT": data['gpt_summary_prompt_v2']['prompt'],  
        "GPT_TITLE_PROMPT": data['gpt_title_prompt_v3']['prompt'],  
        "GPT_SIMILARITY_PROMPT": data['gpt_similarity_prompt_v1']['prompt'],  
        "GPT_WEEKLY_SUMMARY_PROMPT": data['gpt_weekly_summary_prompt_v1']['prompt']  
    }  
  
def load_targets_config(): 
    """
    讀取目標主題、爬取的root Url、顯示語言、推送到teams的channel webhook
    """ 
    with open('target_config.json', 'r') as f:  
        return json.load(f)  
  
def process_targets(targets, system_prompts):
    """
    根據target_config.json的目標依次爬取更新並總結推送至teams的channel
    並在每週一推送一次上週更新總結
    """
    for target in targets:  
        topic = target['topic_name']  
        root_commits_url = target['root_commits_url']  
        language = target['language']  
        teams_webhook_url = target['teams_webhook_url']  
  
        logger.warning(f"========================= Start to process topic: {topic} =========================")  
        logger.info(f"Root commits url: {root_commits_url}")  
        logger.info(f"Language: {language}")  
        logger.info(f"Teams webhook url: {teams_webhook_url}")  
  
        git_spyder = Spyder(topic, root_commits_url, language, teams_webhook_url, system_prompts)  
        # all_commits = git_spyder.get_all_commits()  
        # selected_commits, latest_crawl_time = git_spyder.select_latest_commits(all_commits)  
        git_spyder.process_commits(git_spyder.latest_commits)  

        this_week_summary = git_spyder.cosmosDB_client.check_weekly_summary(topic, language, root_commits_url)  

        now = datetime.datetime.now()
        seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()    
        if (now.weekday() == 0 and seconds_since_midnight < git_spyder.schedule) or this_week_summary is None:  
            git_spyder.push_weekly_summary()  
        logger.warning(f"Finish processing topic: {topic}")  
    return git_spyder.schedule

def main():
    """
    以循環方式固定時間爬取一次檢測是否有文檔更新
    """
    system_prompts = load_system_prompts()  
    targets = load_targets_config()  
  
    while True:  
        try:  
            schedule = process_targets(targets, system_prompts)  
            logger.warning(f"Waiting for {schedule} seconds")  
            time.sleep(schedule)  
        except Exception as e:  
            logger.exception("Unexpected exception:", e)  
  
if __name__ == "__main__":   
    main()  
