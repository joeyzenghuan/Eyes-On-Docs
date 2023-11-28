from logs import logger

from gpt_reply import *



# 调用GPT4 总结删除和增加的内容
class CallGPT:
    def gpt_summary(self, input_dict, language, gpt_summary_prompt):  
        commit_patch_data = input_dict.get("commits")

        system_message = f"{gpt_summary_prompt} Reply in {language}."

        messages = [
            {
                "role": "system",
                "content": system_message,
            },
            {"role": "user", "content": f"Here are the commit patch data. #####{commit_patch_data} ##### Reply in {language}"},
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
        .replace(".yml", "") \
        .replace("/windows-driver-docs-pr/", "https://learn.microsoft.com/en-us/windows-hardware/drivers/") \
        .replace("windows-driver-docs-pr/", "https://learn.microsoft.com/en-us/windows-hardware/drivers/") \
        .replace("/docs/", "https://learn.microsoft.com/en-us/fabric/") \
        .replace("docs/", "https://learn.microsoft.com/en-us/fabric/")

        logger.warning(f"Correct Links in GPT_Summary Response:\n  {gpt_summary_response}")
        self.commit_history["gpt_commit_patch_data"] = commit_patch_data
        self.commit_history["gpt_summary_response"] = gpt_summary_response
        self.commit_history["gpt_summary_prompt_tokens"] = prompt_tokens
        self.commit_history["gpt_summary_completion_tokens"] = completion_tokens
        self.commit_history["gpt_summary_total_tokens"] = total_tokens

        return gpt_summary_response

    def gpt_title(self, input_, language, gpt_title_prompt):  # 调用GPT生成标题
        system_prompt = f"{gpt_title_prompt} Reply in {language}."
        messages = [
            {
                "role": "system",
                "content": str(system_prompt),
            },
            {"role": "user", "content": str(input_)},
        ]

        logger.info(f"GPT_Title Request body: {messages}")

        gpt_title_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages)

        logger.info(f"GPT_Title Prompt tokens:  {prompt_tokens}")
        logger.info(f"GPT_Title Completion tokens:  {completion_tokens}")
        logger.info(f"GPT_Title Total tokens:  {total_tokens}")

        logger.warning(f"GPT_Title Response:\n {gpt_title_response}")

        self.commit_history["gpt_title_response"] = gpt_title_response
        self.commit_history["gpt_title_prompt_tokens"] = prompt_tokens
        self.commit_history["gpt_title_completion_tokens"] = completion_tokens
        self.commit_history["gpt_title_total_tokens"] = total_tokens

        return gpt_title_response
    def get_similarity(self, input_dict, language, lastest_commit_in_cosmosdb, gpt_similarity_prompt):
        # 
        if lastest_commit_in_cosmosdb is None:
            return "0"
        else:
            previous_prompt = lastest_commit_in_cosmosdb["gpt_commit_patch_data"]

            commit_patch_data = input_dict.get("commits")

            system_message = f"{gpt_similarity_prompt} Reply Reasoning in {language}."

            messages = [
                {
                    "role": "system",
                    "content": system_message,
                },
                # {"role": "user", "content": str(input_dict)},
                {"role": "user", "content": f"""Patch 1 data:  
                                                {previous_prompt}
                                                
                                                Patch 2 data:  
                                                {commit_patch_data}
                                                
                                                Output (1 for similar, 0 for not similar): 
                                                [Placeholder for the AI's binary output]  
                                                
                                                Reasoning:  
                                                [Placeholder for the AI's explanation]
                                                """},
            ]

            logger.info(f"GPT_Similarity Request body: {messages}")

            gpt_similarity_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages)
            
            logger.warning(f"GPT_Similarity Response:\n  {gpt_similarity_response}")
            logger.info(f"GPT_Similarity Prompt tokens:  {prompt_tokens}")
            logger.info(f"GPT_Similarity Completion tokens:  {completion_tokens}")
            logger.info(f"GPT_Similarity Total tokens:  {total_tokens}")

            return gpt_similarity_response

    def get_weekly_summary(self, language, weekly_commit_list, gpt_weekly_summary_prompt):
        # 
        
        init_prompt = "Here are the document titles and summaries for this week's updates from Microsoft Learn:\n\n"
        for commit in weekly_commit_list:
            if commit["gpt_title_response"][0] == "1":
                init_prompt += commit["gpt_title_response"][2:] + "\n\n" + commit["gpt_summary_response"] + "\n\n"
        prompt = init_prompt + "Please format the updates in a numbered list, with each entry containing the title tag, title, summary, and link, prioritized by their significance with the most important updates at the top."

        messages = [
            {
                "role": "system",
                "content": f"{gpt_weekly_summary_prompt}\n  Reply Reasoning in {language}.",
            },
            {"role": "user", "content": prompt},
        ]

        logger.info(f"GPT_Weekly_Summary Request body: {messages}")

        gpt_weekly_summary_response, prompt_tokens, completion_tokens, total_tokens = get_gpt_response(messages, max_tokens=2000)
        
        logger.warning(f"GPT_Weekly_Summary Response:\n  {gpt_weekly_summary_response}")
        logger.info(f"GPT_Weekly_Summary Prompt tokens:  {prompt_tokens}")
        logger.info(f"GPT_Weekly_Summary Completion tokens:  {completion_tokens}")
        logger.info(f"GPT_Weekly_Summary Total tokens:  {total_tokens}")

        self.commit_history["gpt_weekly_summary_response"] = gpt_weekly_summary_response
        self.commit_history["gpt_weekly_summary_prompt_tokens"] = prompt_tokens
        self.commit_history["gpt_weekly_summary_completion_tokens"] = completion_tokens
        self.commit_history["gpt_weekly_summary_total_tokens"] = total_tokens

        return gpt_weekly_summary_response