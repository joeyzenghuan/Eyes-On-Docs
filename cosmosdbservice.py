import os
import re
import uuid
from datetime import datetime, timedelta
from collections import Counter
# from flask import Flask, request
from azure.identity import DefaultAzureCredential  
from azure.cosmos import CosmosClient, PartitionKey, exceptions
  
class CosmosConversationClient:
    
    def __init__(self, cosmosdb_endpoint: str, credential: any, database_name: str, container_name: str):
        self.cosmosdb_endpoint = cosmosdb_endpoint
        self.credential = credential
        self.database_name = database_name
        self.container_name = container_name
        self.cosmosdb_client = CosmosClient(self.cosmosdb_endpoint, credential=credential)
        self.database_client = self.cosmosdb_client.get_database_client(database_name)
        self.container_client = self.database_client.get_container_client(container_name)

    def check_weekly_summary(self, topic, language, root_commits_url, sort_order = 'DESC'):
        parameters = [
            {
                'name': '@topic',
                'value': topic
            },
            {
                'name': '@language',
                'value': language
            },
            {
                'name': '@root_commits_url',
                'value': root_commits_url
            }
        ]
  
        # 取得當前時間的UTC  
        now = datetime.utcnow()  
        
        # 計算今天是這周的第幾天，週一是0，週日是6  
        today_weekday = now.weekday()  
        
        # 計算這周的週一  
        this_monday = now - timedelta(days=(today_weekday))
        
        # 計算這周的週日（週一加6天）  
        this_sunday = this_monday + timedelta(days=6)
        
        # 格式化為ISO8601字符串  
        this_monday_str = this_monday.strftime("%Y-%m-%dT00:00:00")  
        this_sunday_str = this_sunday.strftime('%Y-%m-%dT23:59:59')  
        
        query = f"""  
            SELECT * FROM c  
            WHERE  
                CONTAINS(LOWER(c.teams_message_jsondata.title), '[weekly summary]') 
                AND c.topic = @topic  
                AND c.root_commits_url = @root_commits_url  
                AND c.language = @language 
                AND c.log_time >= '{this_monday_str}'  
                AND c.log_time <= '{this_sunday_str}'  
            ORDER BY c.log_time {sort_order}  
        """  
        # 執行查詢  
        weekly_summary_list = list(self.container_client.query_items(  
            query=query,  
            parameters=parameters,  
            enable_cross_partition_query=True))  

        if len(weekly_summary_list) == 0:
            return None
        else:
            return weekly_summary_list

    def create_commit_history(self, history_dict: dict):
        
        history_dict['id'] = str(uuid.uuid4())
        history_dict['log_time'] = datetime.utcnow().isoformat()
        resp = self.container_client.upsert_item(history_dict)  
        if resp:
            # ## update the parent conversations's updatedAt field with the current message's createdAt datetime value
            # conversation = self.get_conversation(user_id, conversation_id)
            # conversation['updatedAt'] = message['createdAt']
            # self.upsert_conversation(conversation)
            return resp
        else:
            return False
        
    def create_message(self, conversation_id, user_id, input_message: dict):
        message = {
            'id': str(uuid.uuid4()),
            'type': 'message',
            'userId' : user_id,
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat(),
            'conversationId' : conversation_id,
            'role': input_message['role'],
            'content': input_message['content']
        }
        
        resp = self.container_client.upsert_item(message)  
        if resp:
            ## update the parent conversations's updatedAt field with the current message's createdAt datetime value
            conversation = self.get_conversation(user_id, conversation_id)
            conversation['updatedAt'] = message['createdAt']
            self.upsert_conversation(conversation)
            return resp
        else:
            return False
    
    def create_conversation(self, user_id, title = ''):
        conversation = {
            'id': str(uuid.uuid4()),  
            'type': 'conversation',
            'createdAt': datetime.utcnow().isoformat(),  
            'updatedAt': datetime.utcnow().isoformat(),  
            'userId': user_id,
            'title': title
        }
        ## TODO: add some error handling based on the output of the upsert_item call
        resp = self.container_client.upsert_item(conversation)  
        if resp:
            return resp
        else:
            return False
        
    # def create_commit_history(self, teststring: str):
    #     message = {
    #         'id': str(uuid.uuid4()),
    #         'type': 'message',
    #         'history' : teststring,
    #         'createdAt': datetime.utcnow().isoformat(),
    #         'abc' : 'abc'
    #         # 'userId' : user_id,
    #         # 'createdAt': datetime.utcnow().isoformat(),
    #         # 'updatedAt': datetime.utcnow().isoformat(),
    #         # 'conversationId' : conversation_id,
    #         # 'role': input_message['role'],
    #         # 'content': input_message['content']
    #     }
        
    #     resp = self.container_client.upsert_item(message)  
    #     if resp:
    #         # ## update the parent conversations's updatedAt field with the current message's createdAt datetime value
    #         # conversation = self.get_conversation(user_id, conversation_id)
    #         # conversation['updatedAt'] = message['createdAt']
    #         # self.upsert_conversation(conversation)
    #         return resp
    #     else:
    #         return False
    
    # def create_commit_history(self, gpt_title_response, gpt_summary_response, commit_url, time_, language):
    #     message = {
    #         'id': str(uuid.uuid4()),
    #         'type': 'commit_history',
    #         'gpt_title_response' : gpt_title_response,
    #         'gpt_summary_response': gpt_summary_response,
    #         'commit_url' : commit_url,
    #         'commit_time' : str(time_),
    #         'language' : language
    #         # 'userId' : user_id,
    #         # 'createdAt': datetime.utcnow().isoformat(),
    #         # 'updatedAt': datetime.utcnow().isoformat(),
    #         # 'conversationId' : conversation_id,
    #         # 'role': input_message['role'],
    #         # 'content': input_message['content']
    #     }
        
    #     resp = self.container_client.upsert_item(message)  
    #     if resp:
    #         # ## update the parent conversations's updatedAt field with the current message's createdAt datetime value
    #         # conversation = self.get_conversation(user_id, conversation_id)
    #         # conversation['updatedAt'] = message['createdAt']
    #         # self.upsert_conversation(conversation)
    #         return resp
    #     else:
    #         return False
    
    def delete_conversation(self, user_id, conversation_id):
        conversation = self.container_client.read_item(item=conversation_id, partition_key=user_id)        
        if conversation:
            resp = self.container_client.delete_item(item=conversation_id, partition_key=user_id)
            return resp
        else:
            return True

    def delete_messages(self, conversation_id, user_id):
        ## get a list of all the messages in the conversation
        messages = self.get_messages(user_id, conversation_id)
        response_list = []
        if messages:
            for message in messages:
                resp = self.container_client.delete_item(item=message['id'], partition_key=user_id)
                response_list.append(resp)
            return response_list
      
    def ensure(self):
        try:
            if not self.cosmosdb_client or not self.database_client or not self.container_client:
                return False
            
            container_info = self.container_client.read()
            if not container_info:
                return False
            
            return True
        except:
            return False

    def get_lastest_commit(self, topic, language, root_commits_url, sort_order = 'DESC'):
        parameters = [
            {
                'name': '@topic',
                'value': topic
            },
            {
                'name': '@language',
                'value': language
            },
            {
                'name': '@root_commits_url',
                'value': root_commits_url
            }
        ]
        query = f"SELECT TOP 1 * FROM c where c.topic = @topic and c.root_commits_url = @root_commits_url and c.language = @language order by c.commit_time {sort_order}"
        lastest_commit = list(self.container_client.query_items(query=query, parameters=parameters,
                                                                               enable_cross_partition_query =True))
        ## if no conversations are found, return None
        if len(lastest_commit) == 0:
            return None
        else:
            return lastest_commit[0]

    def get_commit_history(self):
        # parameters = [
        #     {
        #         'name': '@conversationId',
        #         'value': conversation_id
        #     },
        #     {
        #         'name': '@userId',
        #         'value': user_id
        #     }
        # ]
        # query = f"SELECT * FROM c WHERE c.conversationId = @conversationId AND c.type='message' AND c.userId = @userId ORDER BY c.timestamp ASC"
        query = f"SELECT * FROM c"
        messages = list(self.container_client.query_items(query=query, enable_cross_partition_query =True))
        ## if no messages are found, return false
        if len(messages) == 0:
            return []
        else:
            return messages

    def get_weekly_commit(self, topic, language, root_commits_url, sort_order = 'DESC'):
        parameters = [
            {
                'name': '@topic',
                'value': topic
            },
            {
                'name': '@language',
                'value': language
            },
            {
                'name': '@root_commits_url',
                'value': root_commits_url
            }
        ]

        # 取得當前時間的UTC  
        now = datetime.utcnow()  
        
        # 計算今天是這周的第幾天，週一是0，週日是6  
        today_weekday = now.weekday()  
        
        # 計算上周的週一  
        last_monday = now - timedelta(days=(today_weekday+7))
        
        # 計算上周的週日（週一加6天）  
        last_sunday = last_monday + timedelta(days=6)
        
        # 格式化為ISO8601字符串  
        last_monday_str = last_monday.strftime("%Y-%m-%dT00:00:00")  
        last_sunday_str = last_sunday.strftime('%Y-%m-%dT23:59:59')  
        
        query = f"""  
            SELECT * FROM c  
            WHERE  
                c.topic = @topic  
                AND c.root_commits_url = @root_commits_url  
                AND c.language = @language  
                AND IS_DEFINED(c.gpt_title_response) 
                AND c.status = "post" 
                AND NOT IS_DEFINED(c.gpt_weekly_summary_tokens)
                AND c.commit_time >= '{last_monday_str}'  
                AND c.commit_time <= '{last_sunday_str}'  
            ORDER BY c.commit_time {sort_order}  
        """  
        # query = f"SELECT TOP 1 *FROM c WHERE c.topic = @topic AND c.root_commits_url = @root_commits_url AND c.language = @language AND c.commit_time >= (DateTimeOffset() - 7) ORDER BY c.commit_time {sort_order}"
        weekly_commit_list = list(self.container_client.query_items(query=query, parameters=parameters,
                                                                               enable_cross_partition_query =True))
        ## if no conversations are found, return None
        if len(weekly_commit_list) == 0:
            return None
        else:
            return weekly_commit_list
        
    def get_conversations(self, user_id, sort_order = 'DESC'):
        parameters = [
            {
                'name': '@userId',
                'value': user_id
            }
        ]
        query = f"SELECT * FROM c where c.userId = @userId and c.type='conversation' order by c.updatedAt {sort_order}"
        conversations = list(self.container_client.query_items(query=query, parameters=parameters,
                                                                               enable_cross_partition_query =True))
        ## if no conversations are found, return None
        if len(conversations) == 0:
            return []
        else:
            return conversations

    def get_conversation(self, user_id, conversation_id):
        parameters = [
            {
                'name': '@conversationId',
                'value': conversation_id
            },
            {
                'name': '@userId',
                'value': user_id
            }
        ]
        query = f"SELECT * FROM c where c.id = @conversationId and c.type='conversation' and c.userId = @userId"
        conversation = list(self.container_client.query_items(query=query, parameters=parameters,
                                                                               enable_cross_partition_query =True))
        ## if no conversations are found, return None
        if len(conversation) == 0:
            return None
        else:
            return conversation[0]
 
    def get_messages(self, user_id, conversation_id):
        parameters = [
            {
                'name': '@conversationId',
                'value': conversation_id
            },
            {
                'name': '@userId',
                'value': user_id
            }
        ]
        query = f"SELECT * FROM c WHERE c.conversationId = @conversationId AND c.type='message' AND c.userId = @userId ORDER BY c.timestamp ASC"
        messages = list(self.container_client.query_items(query=query, parameters=parameters,
                                                                     enable_cross_partition_query =True))
        ## if no messages are found, return false
        if len(messages) == 0:
            return []
        else:
            return messages

    def get_value_list(self, name):
        if name == "tag":
            query = 'SELECT c.gpt_title_response FROM c'  
            items = list(self.container_client.query_items(  
                query=query,  
                enable_cross_partition_query=True  
            ))  
            import re
            # 正则表达式，用于匹配括号内的内容  
            pattern = re.compile(r"\[(.*?)\]")  
            
            # 遍历查询结果  
            extracted_data = []  
            for item in items:  
                title_response = item.get('gpt_title_response', '')  
                matches = pattern.findall(title_response)  
                if matches:  
                    # 每个匹配项都是括号内的文本  
                    extracted_data.extend(matches)
            # 使用Counter计算每个短语的出现次数，并按计数降序排序  
            counter = Counter(extracted_data)  
            sorted_data = counter.most_common()  # 返回一个列表，其中包含出现次数的降序排列的元素和它们的计数
            sorted_elements = [element for element, count in sorted_data]
            count = [count for element, count in sorted_data] 
            return ["Select All"] + sorted_elements, count
        else:
            query = f"SELECT c.{name} FROM c"  
            message = list(self.container_client.query_items(query=query, enable_cross_partition_query=True))
            if len(message) == 0:
                return ["None"]
            counts = Counter(item.get(name, '') for item in message if item)  

            sorted_value_count_pairs = sorted(counts.items(), key=lambda pair: pair[1], reverse=True)  
    
            sorted_values  = [str(name) for name, count in sorted_value_count_pairs]  
            count  = [count for name, count in sorted_value_count_pairs] 

            return ["Select All"] + sorted_values, count

    def get_commit_time_list(self):
        query = f"SELECT c.commit_time FROM c ORDER BY c.commit_time ASC"  
        
        value_list = []  
        message = list(self.container_client.query_items(query=query, enable_cross_partition_query=True))
        if len(message) == 0:
            return None
        for item in message:
            if item == {}:
                continue
            if str(item["commit_time"]) not in value_list: 
                value_list.append(str(item["commit_time"])) 
        return value_list
    
    # def get_current_select(self, topic, language, status, t, start_time, end_time):
    #     query_parameters = {
    #         'topic': topic,
    #         'language': language,
    #         'status': status
    #     }
    #     # Build query conditions
    #     query_conditions = []
    #     for param, value in query_parameters.items():
    #         if value is not None and value != "Select All":
    #             query_conditions.append(f"c.{param} = @{param}")

    #     # Join query conditions
    #     query_condition_str = " AND ".join(query_conditions)
    #     if query_condition_str:
    #         query_condition_str = "WHERE " + query_condition_str + " AND"
    #     else:
    #         query_condition_str = "WHERE "

    #     # Complete query statement
    #     query = f"""
    #     SELECT * FROM c
    #     {query_condition_str} 
    #         c.commit_time >= "{start_time}" 
    #         AND c.commit_time <= "{end_time}"
    #     ORDER BY c.commit_time DESC
    #     """

    #     parameters = [
    #         {'name': f'@{k}', 'value': v}
    #         for k, v in query_parameters.items()
    #         if v is not None and v != "Select All"
    #     ]
    #     if len(parameters) == 0:
    #         parameters = None 
    #     # Execute query
    #     print(query, parameters)
    #     try:
    #         items = list(self.container_client.query_items(
    #             query=query,
    #             parameters=parameters,
    #             enable_cross_partition_query=True
    #         ))
    #     except exceptions.CosmosHttpResponseError as e:
    #         print(f"An error occurred: {e.message}")
    #     if len(items) == 0:
    #         return None
    #     else: 
    #         return items
    

    def get_current_select(self, topic, language, status, tag, post, start_time, end_time):
        query_parameters = {
            'topic': topic,
            'language': language,
            'status': status,
            'gpt_title_response': tag
        }
        # Build query conditions
        query_conditions = []
        for param, value in query_parameters.items():
            if value is not None and value != "Select All":
                if param == 'gpt_title_response':
                    query_conditions.append(f"CONTAINS(c.gpt_title_response, '{value}')")
                else:
                    query_conditions.append(f"c.{param} = @{param}")
        if post == 'Weekly Summary':
            query_conditions.append(f"CONTAINS(c.teams_message_jsondata.title, '[Weekly Summary]') OR CONTAINS(c.root_commiteams_message_jsondatats_url.title, '[Weekly Summary]')")
        # Join query conditions
        query_condition_str = " AND ".join(query_conditions)
        if query_condition_str:
            query_condition_str = "WHERE " + query_condition_str + " AND"
        else:
            query_condition_str = "WHERE "
        # query_condition_str.replace("")
        # Complete query statement
        query = f"""
        SELECT * FROM c
        {query_condition_str} 
            c.commit_time >= "{start_time}"
            AND c.commit_time <= "{end_time}"
        ORDER BY c.commit_time DESC
        """
        parameters = [
            {'name': f'@{k}', 'value': v}
            for k, v in query_parameters.items()
            if v is not None and v != "Select All"
        ]
        # Add special parameters for the time range
        if len(parameters) == 0:
            parameters = None 
        items = []
        # Execute query
        try:
            items = list(self.container_client.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
        except exceptions.CosmosHttpResponseError as e:
            print(f"An error occurred: {e.message}")
            # Handle the exception as needed, e.g., re-raise or return an empty list
            return None  
        if len(items) == 0:  
            return None
        
        # Extract values inside brackets from the 'gpt_title_response' field
        bracket_values = []
        pattern = re.compile(r"\[([^\]]+)\]")
        for item in items:
            matches = pattern.findall(item.get('gpt_title_response', ''))
            item['tag'] = matches
            bracket_values.extend(matches)

        # Count occurrences and sort by descending order
        value_counts = Counter(bracket_values)
        sorted_values = [value for value, count in value_counts.most_common()]
        count = [count for value, count in value_counts.most_common()]

        return items, sorted_values, count

    def get_timestamp(self, name, start_time, end_time):
        query = f"""  
            SELECT c.topic
            FROM c  
            WHERE  
                c.commit_time >= "{start_time}" AND  
                c.commit_time <= "{end_time}"  
            GROUP BY c.topic  
            ORDER BY c.topic  
        """
        print(query)
        # Add special parameters for the time range
        try:  
            results = list(self.container_client.query_items(  
                query=query,
                enable_cross_partition_query=True  
            ))  
            print(results)
        except exceptions.CosmosHttpResponseError as e:  
            print(f"An error occurred: {e.message}")

    def upsert_conversation(self, conversation):
        resp = self.container_client.upsert_item(conversation)
        if resp:
            return resp
        else:
            return False
