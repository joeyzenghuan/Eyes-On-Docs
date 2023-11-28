from logs import logger  
from gpt_reply import get_gpt_response  
  
  
class CallGPT:  

    def correct_links(self, response):  
        """  
        修正响应中的链接。  
        :param response: GPT模型的回复  
        :return: 修正后的回复  
        """  
        replacements = {  
            "/articles/": "https://learn.microsoft.com/en-us/azure/",  
            "articles/": "https://learn.microsoft.com/en-us/azure/", 
            ".md": "",  
            ".yml": "",  
            "/windows-driver-docs-pr/": "https://learn.microsoft.com/en-us/windows-hardware/drivers/",  
            "windows-driver-docs-pr/": "https://learn.microsoft.com/en-us/windows-hardware/drivers/",  
            "/docs/": "https://learn.microsoft.com/en-us/fabric/",  
            "docs/": "https://learn.microsoft.com/en-us/fabric/"  
        }  
        for old, new in replacements.items():  
            response = response.replace(old, new)  
        logger.warning(f"Correct Links in GPT_Summary Response:\n  {response}")  
        return response  
  
    def update_commit_history(self, key, value):  
        """  
        更新提交历史记录。  
        :param key: 记录的键  
        :param value: 记录的值  
        """  
        self.commit_history[key] = value  
    def gpt_summary(self, input_dict, language, gpt_summary_prompt):  
        """  
        使用GPT模型总结提交的更改内容。  
        :param input_dict: 包含提交信息的字典  
        :param language: 回复的语言  
        :param gpt_summary_prompt: 提示信息  
        :return: GPT模型的回复  
        """  
        commit_patch_data = input_dict.get("commits")  
        system_message = f"{gpt_summary_prompt} Reply in {language}."  
  
        # 构建消息列表，用于发送给GPT模型  
        messages = [  
            {"role": "system", "content": system_message},  
            {"role": "user", "content": f"Here are the commit patch data. #####{commit_patch_data} ##### Reply in {language}"},  
        ]  
  
        # 记录请求信息  
        logger.info(f"GPT_Summary Request body: {messages}")  
  
        # 获取GPT模型的回复  
        gpt_summary_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages)  
  
        # 记录GPT模型的回复及其token信息  
        logger.warning(f"GPT_Summary Response:\n  {gpt_summary_response}")  
        logger.info(f"GPT_Summary Tokens: Prompt {prompt_tokens}, Completion {completion_tokens}, Total {total_tokens}")  
  
        # 替换响应中的链接  
        gpt_summary_response = self.correct_links(gpt_summary_response)  
  
        # 更新提交历史记录  
        self.update_commit_history("gpt_commit_patch_data", commit_patch_data)  
        self.update_commit_history("gpt_summary_response", gpt_summary_response)  
        self.update_commit_history("gpt_summary_tokens", {  
            "prompt": prompt_tokens,  
            "completion": completion_tokens,  
            "total": total_tokens  
        })  
  
        return gpt_summary_response  
  
    def gpt_title(self, input_, language, gpt_title_prompt):  
        """  
        使用GPT模型生成标题。  
        :param input_: 输入内容  
        :param language: 回复的语言  
        :param gpt_title_prompt: 提示信息  
        :return: GPT模型的回复  
        """  
        system_prompt = f"{gpt_title_prompt} Reply in {language}."  
        messages = [  
            {"role": "system", "content": system_prompt},  
            {"role": "user", "content": input_},  
        ]  
  
        # 记录请求信息  
        logger.info(f"GPT_Title Request body: {messages}")  
  
        # 获取GPT模型的回复  
        gpt_title_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages)  
  
        # 记录GPT模型的回复及其token信息  
        logger.warning(f"GPT_Title Response:\n {gpt_title_response}")  
        logger.info(f"GPT_Title Tokens: Prompt {prompt_tokens}, Completion {completion_tokens}, Total {total_tokens}")  
  
        # 更新提交历史记录  
        self.update_commit_history("gpt_title_response", gpt_title_response)  
        self.update_commit_history("gpt_title_tokens", {  
            "prompt": prompt_tokens,  
            "completion": completion_tokens,  
            "total": total_tokens  
        })  
  
        return gpt_title_response  
  
    

    def get_weekly_summary(self, language, weekly_commit_list, gpt_weekly_summary_prompt):  
        """  
        获取一周 commit 的总结  
  
        :param language: 语言  
        :param weekly_commit_list: 一周的 commit 列表  
        :param gpt_weekly_summary_prompt: GPT 周总结提示信息  
        :return: GPT 周总结响应  
        """  
        # 构建初始提示信息  
        init_prompt = "Here are the document titles and summaries for this week's updates from Microsoft Learn:\n\n"  
        for commit in weekly_commit_list:  
            if commit["gpt_title_response"][0] == "1":  
                init_prompt += f"{commit['gpt_title_response'][2:]}\n\n{commit['gpt_summary_response']}\n\n"  
  
        prompt = init_prompt + "Please format the updates in a numbered list, with each entry containing the title tag, title, summary, and link, prioritized by their significance with the most important updates at the top."  
  
        messages = [  
            {"role": "system", "content": f"{gpt_weekly_summary_prompt}\n  Reply Reasoning in {language}."},  
            {"role": "user", "content": prompt},  
        ]  
  
        logger.info(f"GPT_Weekly_Summary Request body: {messages}")  
  
        # 获取 GPT 周总结响应  
        gpt_weekly_summary_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages, max_tokens=2000)  
          
        # 记录日志  
        logger.warning(f"GPT_Weekly_Summary Response:\n  {gpt_weekly_summary_response}")  
        logger.info(f"GPT_Weekly_Summary Tokens: Prompt {prompt_tokens}, Completion {completion_tokens}, Total {total_tokens}")    
  
        # 更新 commit 历史记录  
        self.update_commit_history("gpt_weekly_summary_response", gpt_weekly_summary_response)  
        self.update_commit_history("gpt_weekly_summary_tokens", {  
            "prompt": prompt_tokens,  
            "completion": completion_tokens,  
            "total": total_tokens  
        })  

        return gpt_weekly_summary_response  
  
    def get_similarity(self, input_dict, language, latest_commit_in_cosmosdb, gpt_similarity_prompt):  
        """  
        获取两个 commit 的相似度  
  
        :param input_dict: 输入数据字典，包含 commits 信息  
        :param language: 语言  
        :param latest_commit_in_cosmosdb: CosmosDB 中的最新 commit 数据  
        :param gpt_similarity_prompt: GPT 相似度提示信息  
        :return: GPT 相似度响应  
        """  
        if latest_commit_in_cosmosdb is None:  
            return "0"  
  
        previous_prompt = latest_commit_in_cosmosdb["gpt_commit_patch_data"]  
        commit_patch_data = input_dict.get("commits")  
        system_message = f"{gpt_similarity_prompt} Reply Reasoning in {language}."  
  
        messages = [  
            {"role": "system", "content": system_message},  
            {"role": "user", "content": f"Patch 1 data:\n{previous_prompt}\n\nPatch 2 data:\n{commit_patch_data}\n\nOutput (1 for similar, 0 for not similar):\n[Placeholder for the AI's binary output]\n\nReasoning:\n[Placeholder for the AI's explanation]"},  
        ]  
  
        logger.info(f"GPT_Similarity Request body: {messages}")  
  
        # 获取 GPT 相似度响应  
        gpt_similarity_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages)  
          
        # 记录日志  
        logger.warning(f"GPT_Similarity Response:\n  {gpt_similarity_response}")  
        logger.info(f"GPT_Similarity Tokens: Prompt {prompt_tokens}, Completion {completion_tokens}, Total {total_tokens}")    

        return gpt_similarity_response  
  
    