import requests  
from bs4 import BeautifulSoup  
import datetime  
from logs import logger  

class CommitFetcher:  
    topic_path : str = ""
    def get_all_commits(self, root_commits_url, headers={}):  
        logger.info(f"Commit Root page: {root_commits_url}")  

        # 使用 'path=' 作为分隔符分割字符串
        parts = root_commits_url.split('path=')
        # 获取 'path=' 后面的部分
        self.topic_path = parts[1] if len(parts) > 1 else None

  
        # 獲取網頁響應  
        # response = requests.get(root_commits_url, headers=headers).text  
        response = self._make_request_to_json(root_commits_url, headers=headers)
  

  
        # 初始化數據存儲列表  
        precise_time_list = []  
        commits_url_list = []  

        #解析每個commits
        for item in response:

            # if item['commit']['verification']['verified']== True:
            # 不管是否verified，都爬取
            if True:
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
    
    
        ########################老代码 网页爬虫#########################################
        # # 解析HTML  
        # soup = BeautifulSoup(response, "html.parser")  
      
        # # 找到每天的commits集合  
        # commits_per_day = soup.find_all("div", {"class": "TimelineItem-body"})  
  
        # # 解析每個commits集合  
        # for item in commits_per_day:  
        #     # 提取並解析時間信息  
        #     time_elements = item.find_all("relative-time")  
        #     for time_element in time_elements:  
        #         datetime_str = time_element["datetime"]  
        #         precise_time = datetime.datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")  
        #         precise_time_list.append(precise_time)  
  
        #     # 提取commits的URL  
        #     for div in item.find_all("div", {"class": "flex-auto min-width-0 js-details-container Details"}):  
        #         commit_url = div.find('a', 'Link--primary text-bold js-navigation-open markdown-title').get('href')  
        #         full_url = f"https://github.com{commit_url}"  
        #         commits_url_list.append(full_url)  
  
        # # 將時間和URL打包成字典  
        # commits_dic_time_url = dict(zip(precise_time_list, commits_url_list))  
        # return commits_dic_time_url  
        #################################################################


    def get_change_from_each_url(self, time, commit_url, max_input_token, headers={}):  
        logger.warning(f"Getting changes from url: {commit_url}")  

        # 获取具体commits信息，json file 
        # response = requests.get(commit_url, headers=headers).json()
        response = self._make_request_to_json(commit_url, headers=headers)



        #创建与原始版本类似的patch数据
        commit_response=response['files']
        # result_list=[] #构建结果列表
        commit_patch_data = ""
        for item in commit_response:
            if "patch" in item.keys() and "filename" in item.keys():

                # 有时一个commit会有多个文件的patch，这里只取topic_path下的patch
                if item["filename"].startswith(self.topic_path) or self.topic_path is None:
                    patch_data="Original Path:"+item["filename"]+"\r\n"+item["patch"]+"\n\n"
                    commit_patch_data += patch_data
                    # if len(patch_data) >= max_input_token:
                    #     result_list.append(patch_data[:max_input_token])
                    # else:
                    #     result_list.append(patch_data)
        
        commit_patch_data = commit_patch_data[:max_input_token] if len(commit_patch_data) >= max_input_token else commit_patch_data

        logger.debug(f"Get commit_patch_data: {commit_patch_data}")  
        
        return commit_patch_data
  
        # # 獲取commit頁面的內容  
        # response = self._make_request(commit_url)  
  
        # # 解析commit頁面  
        # soup = BeautifulSoup(response, "html.parser")  
        # commit_title = soup.find("div", class_="commit-title markdown-title").get_text(strip=True) if soup.find("div", class_="commit-title markdown-title") else ""  
        # commit_desc = soup.find("div", {"class": "commit-desc"}).pre.get_text(strip=True) if soup.find("div", {"class": "commit-desc"}) else ""  
  
        # # 獲取patch數據  
        # patch_url = commit_url + ".patch"  
        # patch_data = self._make_request(patch_url, is_stream=True)  
  
        # # 構建結果字典  
        # result_dic = {  
        #     "commits": patch_data[:max_input_token] if len(patch_data) >= max_input_token else patch_data,  
        #     "urls": []  
        # }  
  
        # logger.debug(f"Get Change result_dic: {result_dic}")  
  
        # return result_dic, time, f"{commit_title}, {commit_desc}", commit_url  

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
            return response.text  
        except requests.RequestException as e:  
            logger.error(f"Request exception for URL: {url}", exc_info=e)  
            return "Error"  
        
    def _make_request_to_json(self, url, is_stream=False, headers={}):  
        try:  
            response = requests.get(url, stream=is_stream, headers=headers)  
            response.raise_for_status()  
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
