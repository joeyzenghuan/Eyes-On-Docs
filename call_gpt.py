from logs import logger  
from gpt_reply import get_gpt_response, get_gpt_structured_response  
import tiktoken
  
class CallGPT:  

    def correct_links(self, response, url_mapping):  
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
            "windows-driver-docs-pr/": "https://learn.microsoft.com/en-us/windows-hardware/drivers/"
        }  

        logger.warning(f"url_mapping: {url_mapping}")
        # 检查'mapping'键是否存在，如果存在，则将其加入到已存在的字典中
        if url_mapping is not None:
            replacements.update(url_mapping)
        print(replacements)

        for old, new in replacements.items():  
            response = response.replace(old, new)  
        logger.warning(f"Correct Links in GPT_Summary Response:\n  {response}")  
        return response  
  
    
    def gpt_summary(self, commit_patch_data, language, gpt_summary_prompt, url_mapping):  
        """  
        使用GPT模型总结提交的更改内容。  
        :param input_dict: 包含提交信息的字典  
        :param language: 回复的语言  
        :param gpt_summary_prompt: 提示信息  
        :return: GPT模型的回复  
        """  
        # commit_patch_data = input_dict.get("commits")  
        system_message = f"{gpt_summary_prompt} Reply in {language}."  
  
        # 构建消息列表，用于发送给GPT模型  
        messages = [  
            {"role": "system", "content": system_message},  
            {"role": "user", "content": f"Here are the commit patch data. #####{commit_patch_data} ##### Reply in {language}"},  
        ]  
  
        # 记录请求信息  
        logger.debug(f"GPT_Summary Request body: {messages}")  
  
        # 获取GPT模型的回复  
        gpt_summary_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages)  
  
        # 记录GPT模型的回复及其token信息  
        logger.warning(f"GPT_Summary Response:\n  {gpt_summary_response}")  
        logger.info(f"GPT_Summary Tokens: Prompt {prompt_tokens}, Completion {completion_tokens}, Total {total_tokens}")  
  
        # 替换响应中的链接  
        gpt_summary_response = self.correct_links(gpt_summary_response, url_mapping)  
   
        gpt_summary_tokens = {  
            "prompt": prompt_tokens,  
            "completion": completion_tokens,  
            "total": total_tokens  
        }
  
        return gpt_summary_response, gpt_summary_tokens, commit_patch_data
  
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
        logger.debug(f"GPT_Title Request body: {messages}")  
  
        # 获取GPT模型的回复  
        gpt_title_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages)  
  
        # 记录GPT模型的回复及其token信息  
        logger.warning(f"GPT_Title Response:\n {gpt_title_response}")  
        logger.info(f"GPT_Title Tokens: Prompt {prompt_tokens}, Completion {completion_tokens}, Total {total_tokens}")  
  
        gpt_title_tokens = {  
            "prompt": prompt_tokens,  
            "completion": completion_tokens,  
            "total": total_tokens  
        } 
  
        return gpt_title_response, gpt_title_tokens
  
    

    def generate_weekly_summary_using_weekly_commit_list(self, language, weekly_commit_list, gpt_weekly_summary_prompt, max_input_token):  
        """  
        获取一周 commit 的总结  
  
        :param language: 语言  
        :param weekly_commit_list: 一周的 commit 列表  
        :param gpt_weekly_summary_prompt: GPT 周总结提示信息  
        :return: GPT 周总结响应  
        """  
        if not weekly_commit_list:
            logger.warning("Weekly commit list is empty")
            return None, None
        
        init_prompt = "Here are the document titles and summaries for this week's updates from Microsoft Learn:\n\n"  
        end_prompt = "Please format the updates in a numbered list, with each entry containing the title tag, title, summary, and link, prioritized by their significance with the most important updates at the top."
        
        post_data = False
        skipped_commits = 0
        
        for commit in weekly_commit_list:  
            title_response = commit.get("gpt_title_response", "")
            if not isinstance(title_response, str) or len(title_response) < 1:
                logger.warning(f"Invalid title response for commit: {commit}")
                continue
            
            if title_response[0] == "1":
                summary_response = commit.get("gpt_summary_response", "")
                if not isinstance(summary_response, str):
                    logger.warning(f"Invalid summary response for commit: {commit}")
                    continue
                
                post_data = True
                init_prompt += f"{title_response[2:]}\n\n{summary_response}\n\n"
                
                used_tokens = self.num_tokens_from_string(
                    gpt_weekly_summary_prompt + init_prompt + end_prompt, 
                    "cl100k_base"
                )
                
                if used_tokens > max_input_token:
                    logger.warning(f"Input tokens exceed the limit: {used_tokens} / {max_input_token}")
                    skipped_commits = len(weekly_commit_list) - weekly_commit_list.index(commit)
                    logger.warning(f"Skipped {skipped_commits} commits due to token limit")
                    break

        if not post_data:
            logger.warning("No valid commit data found for weekly summary")
            return None, None

        
        prompt = init_prompt + end_prompt
        messages = [  
            {"role": "system", "content": f"{gpt_weekly_summary_prompt}\n  Reply Reasoning in {language}."},  
            {"role": "user", "content": prompt},  
        ]  
        logger.debug(f"GPT_Weekly_Summary Request body: {messages}")  
  
        # 获取 GPT 周总结响应  
        gpt_weekly_summary_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages, max_tokens=4000)  
          
        # 记录日志  
        logger.debug(f"GPT_Weekly_Summary Response:\n  {gpt_weekly_summary_response}")  
        logger.info(f"**************** GPT_Weekly_Summary Tokens: Prompt {prompt_tokens}, Completion {completion_tokens}, Total {total_tokens}")    

        gpt_weekly_summary_tokens = {  
            "prompt": prompt_tokens,  
            "completion": completion_tokens,  
            "total": total_tokens  
        }

        return gpt_weekly_summary_response, gpt_weekly_summary_tokens
  
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
  
        logger.debug(f"GPT_Similarity Request body: {messages}")  
  
        # 获取 GPT 相似度响应  
        gpt_similarity_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages)  
          
        # 记录日志  
        logger.warning(f"GPT_Similarity Response:\n  {gpt_similarity_response}")  
        logger.info(f"GPT_Similarity Tokens: Prompt {prompt_tokens}, Completion {completion_tokens}, Total {total_tokens}")    

        return gpt_similarity_response  
  
    def gpt_summary_and_title_structured(self, commit_patch_data, language, gpt_structured_prompt, url_mapping):
        """
        使用 structured output 一次性生成摘要和标题
        
        :param commit_patch_data: 提交的补丁数据
        :param language: 回复的语言
        :param gpt_structured_prompt: structured output 的提示词
        :param url_mapping: URL 映射配置
        :return: (gpt_summary, gpt_title, importance_score, importance_score_reasoning, gpt_tokens, commit_patch_data)
        """
        try:
            # 定义 JSON schema
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "document_analysis",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "详细的更新内容摘要"
                            },
                            "title": {
                                "type": "string", 
                                "description": "格式化的标题，格式为：[标签] 具体标题，不包含数字前缀"
                            },
                            "importance_score": {
                                "type": "integer",
                                "description": "重要性评分：1表示重要需要通知，0表示不重要跳过通知",
                                "enum": [0, 1]
                            },
                            "importance_score_reasoning": {
                                "type": "string",
                                "description": "判断重要性的理由"
                            }
                        },
                        "required": ["summary", "title", "importance_score", "importance_score_reasoning"],
                        "additionalProperties": False
                    }
                }
            }
            
            system_message = f"{gpt_structured_prompt} Reply in {language}."
            
            # 构建消息列表
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Here are the commit patch data. #####{commit_patch_data} ##### Reply in {language}"},
            ]
            
            # 记录请求信息
            logger.debug(f"GPT_Structured Request body: {messages}")
            
            # 获取 structured response (不设置max_tokens，使用API默认值)
            structured_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_structured_response(
                messages, response_format
            )
            
            if structured_response is None:
                logger.error("Failed to get structured response from GPT")
                return None, None, None, None, commit_patch_data
                
            # 提取结果
            gpt_summary = structured_response.get("summary", "")
            gpt_title = structured_response.get("title", "")
            importance_score = structured_response.get("importance_score", 0)
            importance_score_reasoning = structured_response.get("importance_score_reasoning", "")
            
            # 修正摘要中的链接
            gpt_summary = self.correct_links(gpt_summary, url_mapping)
            
            # 记录响应和token信息
            logger.warning(f"GPT_Structured Response Summary:\n  {gpt_summary}")
            logger.warning(f"GPT_Structured Response Title:\n  {gpt_title}")
            logger.warning(f"GPT_Structured Importance Score: {importance_score}")
            logger.warning(f"GPT_Structured Importance Score Reasoning: {importance_score_reasoning}")
            logger.info(f"GPT_Structured Tokens: Prompt {prompt_tokens}, Completion {completion_tokens}, Total {total_tokens}")
            
            gpt_tokens = {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": total_tokens
            }
            
            return gpt_summary, gpt_title, importance_score, importance_score_reasoning, gpt_tokens, commit_patch_data
            
        except Exception as e:
            logger.exception("Exception in gpt_summary_and_title_structured:", e)
            return None, None, None, None, None, commit_patch_data
  
    def num_tokens_from_string(self, string: str, encoding_name: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens