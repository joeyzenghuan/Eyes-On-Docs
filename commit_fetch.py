import requests  
from bs4 import BeautifulSoup  
import datetime  
from logs import logger  

class CommitFetcher:  

    def get_all_commits(self, root_commits_url, headers={}):  
        logger.info(f"Commit Root page: {root_commits_url}")  
  
        # 獲取網頁響應  
        response = requests.get(root_commits_url, headers=headers).text  
  
        # 解析HTML  
        soup = BeautifulSoup(response, "html.parser")  
  
        # 初始化數據存儲列表  
        precise_time_list = []  
        commits_url_list = []  
  
        # 找到每天的commits集合  
        commits_per_day = soup.find_all("div", {"class": "TimelineItem-body"})  
  
        # 解析每個commits集合  
        for item in commits_per_day:  
            # 提取並解析時間信息  
            time_elements = item.find_all("relative-time")  
            for time_element in time_elements:  
                datetime_str = time_element["datetime"]  
                precise_time = datetime.datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")  
                precise_time_list.append(precise_time)  
  
            # 提取commits的URL  
            for div in item.find_all("div", {"class": "flex-auto min-width-0 js-details-container Details"}):  
                commit_url = div.find('a', 'Link--primary text-bold js-navigation-open markdown-title').get('href')  
                full_url = f"https://github.com{commit_url}"  
                commits_url_list.append(full_url)  
  
        # 將時間和URL打包成字典  
        commits_dic_time_url = dict(zip(precise_time_list, commits_url_list))  
        return commits_dic_time_url  

  
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
  
    def get_change_from_each_url(self, time, commit_url):  
        logger.warning(f"Getting changes from url: {commit_url}")  
  
        # 獲取commit頁面的內容  
        response = self._make_request(commit_url)  
  
        # 解析commit頁面  
        soup = BeautifulSoup(response, "html.parser")  
        commit_title = soup.find("div", class_="commit-title markdown-title").get_text(strip=True) if soup.find("div", class_="commit-title markdown-title") else ""  
        commit_desc = soup.find("div", {"class": "commit-desc"}).pre.get_text(strip=True) if soup.find("div", {"class": "commit-desc"}) else ""  
  
        # 獲取patch數據  
        patch_url = commit_url + ".patch"  
        patch_data = self._make_request(patch_url, is_stream=True)  
  
        # 構建結果字典  
        result_dic = {  
            "commits": patch_data[:30000] if len(patch_data) >= 30000 else patch_data,  
            "urls": []  
        }  
  
        logger.debug(f"Get Change result_dic: {result_dic}")  
  
        return result_dic, time, f"{commit_title}, {commit_desc}", commit_url  
  
    def _make_request(self, url, is_stream=False, headers={}):  
        try:  
            response = requests.get(url, stream=is_stream, headers=headers)  
            response.raise_for_status()  
            return response.text  
        except requests.RequestException as e:  
            logger.error(f"Request exception for URL: {url}", exc_info=e)  
            return "Error"  
  

if __name__ == "__main__":  
    fetcher = CommitFetcher()  
    all_commits = fetcher.get_all_commits("https://github.com/MicrosoftDocs/azure-docs/commits/main/articles/ai-services/openai/")  
    latest_commits, latest_time = fetcher.select_latest_commits(all_commits, datetime.datetime.now())  
    for commit_time, commit_url in latest_commits.items():  
        change_details = fetcher.get_change_from_each_url(commit_time, commit_url)  
