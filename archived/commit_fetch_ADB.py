import requests  
from bs4 import BeautifulSoup  
import datetime  
from logs import logger  

class CommitFetcher:  
    def get_all_commits(self, root_commits_url, headers={}):  
        logger.info(f"Commit Root page: {root_commits_url}")  
  
        # https://api.github.com/repos/MicrosoftDocs/databricks-pr/commits/main 得到的response是json文件
        response = requests.get(root_commits_url, headers=headers).json()
        
        #初始化数据列表
        precise_time_list = []  
        commits_url_list = []  

        #解析每個commits
        for item in response:

            if item['commit']['verification']['verified']== True:
                #提取时间信息
                datetime_str=datetime_str=item['commit']['author']['date']
                precise_time = datetime.datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")
                precise_time_list.append(precise_time)  
                #提取commits url
                full_url=item['url']
                commits_url_list.append(full_url)  
        #将时间和url打包成dict
        commits_dic_time_url = dict(zip(precise_time_list, commits_url_list))  
        return commits_dic_time_url    

    def get_change_from_each_url(self, time, commit_url, max_input_token, headers={}):  

        logger.warning(f"Getting changes from url: {commit_url}")  

        # 获取具体commits信息，json file 
        response = requests.get(commit_url, headers=headers).json()



        #创建与原始版本类似的patch数据
        commit_response=response['files']
        result_list=[] #构建结果列表
        for item in commit_response:
            if "patch" in item.keys():
                patch_data="Original Path:"+item["filename"]+"\r\n"+item["patch"]
                if len(patch_data) >= max_input_token:
                    result_list.append(patch_data[:max_input_token])
                else:
                    result_list.append(patch_data)
        
        logger.debug(f"Get Change result_list: {result_list}")  
        
        return result_list
        

    def select_latest_commits(self, commits_dic_time_url, start_time):  
        # 篩選出開始時間之後的提交  
        selected_commits = {key: url for key, url in commits_dic_time_url.items() if key > start_time}  
  
        # 按時間排序  
        selected_commits = dict(sorted(selected_commits.items(), key=lambda x: x[0]))  
  
        # 記錄篩選後的提交數量  
        selected_commits_length = len(selected_commits)  
        logger.warning(f"++++++++++++++++++++++++ {selected_commits_length} selected commits: {selected_commits}")  
  
        # 獲取最新的提交時間  
        if selected_commits_length > 0:  
            latest_crawl_time = str(max(selected_commits.keys()))  
            logger.warning(f"Max new commits time: {latest_crawl_time}")  
        else:  
            latest_crawl_time = start_time  
            logger.warning("No new commits")  
  
        # 返回篩選後的提交以及最新的爬取時間  
        return selected_commits, latest_crawl_time 

    def _make_request(self, url, is_stream=False, headers={}):  
        try:  
            response = requests.get(url, stream=is_stream, headers=headers)  
            response.raise_for_status()  
            #return response.text not html,but json
            return response.json()  
        except requests.RequestException as e:  
            logger.error(f"Request exception for URL: {url}", exc_info=e)  
            return "Error"  
  

if __name__ == "__main__":  
    fetcher = CommitFetcher()  
    all_commits = fetcher.get_all_commits("https://github.com/MicrosoftDocs/azure-docs/commits/main/articles/ai-services/openai/")  
    latest_commits, latest_time = fetcher.select_latest_commits(all_commits, datetime.datetime.now())  
    for commit_time, commit_url in latest_commits.items():  
        change_details = fetcher.get_change_from_each_url(commit_time, commit_url)  
