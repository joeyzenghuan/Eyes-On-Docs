import os
import uuid
from datetime import datetime
# from flask import Flask, request
from azure.identity import DefaultAzureCredential  
from azure.cosmos import CosmosClient, PartitionKey  
  
class CosmosConversationClient():
    
    def __init__(self, cosmosdb_endpoint: str, credential: any, database_name: str, container_name: str):
        self.cosmosdb_endpoint = cosmosdb_endpoint
        self.credential = credential
        self.database_name = database_name
        self.container_name = container_name
        self.cosmosdb_client = CosmosClient(self.cosmosdb_endpoint, credential=credential)
        self.database_client = self.cosmosdb_client.get_database_client(database_name)
        self.container_client = self.database_client.get_container_client(container_name)

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

    def create_commit_history(self, teststring: str):
        message = {
            'id': str(uuid.uuid4()),
            'type': 'message',
            'history' : teststring,
            'createdAt': datetime.utcnow().isoformat(),
            'abc' : 'abc'
            # 'userId' : user_id,
            # 'createdAt': datetime.utcnow().isoformat(),
            # 'updatedAt': datetime.utcnow().isoformat(),
            # 'conversationId' : conversation_id,
            # 'role': input_message['role'],
            # 'content': input_message['content']
        }
        
        resp = self.container_client.upsert_item(message)  
        if resp:
            # ## update the parent conversations's updatedAt field with the current message's createdAt datetime value
            # conversation = self.get_conversation(user_id, conversation_id)
            # conversation['updatedAt'] = message['createdAt']
            # self.upsert_conversation(conversation)
            return resp
        else:
            return False
    
    def create_commit_history(self, gpt_title_response, gpt_summary_response, commit_url, time_, language):
        message = {
            'id': str(uuid.uuid4()),
            'type': 'commit_history',
            'gpt_title_response' : gpt_title_response,
            'gpt_summary_response': gpt_summary_response,
            'commit_url' : commit_url,
            'commit_time' : str(time_),
            'language' : language
            # 'userId' : user_id,
            # 'createdAt': datetime.utcnow().isoformat(),
            # 'updatedAt': datetime.utcnow().isoformat(),
            # 'conversationId' : conversation_id,
            # 'role': input_message['role'],
            # 'content': input_message['content']
        }
        
        resp = self.container_client.upsert_item(message)  
        if resp:
            # ## update the parent conversations's updatedAt field with the current message's createdAt datetime value
            # conversation = self.get_conversation(user_id, conversation_id)
            # conversation['updatedAt'] = message['createdAt']
            # self.upsert_conversation(conversation)
            return resp
        else:
            return False
    
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


    # def get_commit_history(self, user_id, conversation_id):
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
    
    def upsert_conversation(self, conversation):
        resp = self.container_client.upsert_item(conversation)
        if resp:
            return resp
        else:
            return False

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
        from datetime import datetime, timedelta  
  
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
        from datetime import datetime, timedelta  
  
        # 取得當前時間的UTC  
        now = datetime.utcnow()  
        
        # 計算今天是這周的第幾天，週一是0，週日是6  
        today_weekday = now.weekday()  
        
        # 計算這周的週一  
        this_monday = now - timedelta(days=today_weekday)  
        
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
