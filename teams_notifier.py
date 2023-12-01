import datetime
import requests
from logs import logger  

class TeamsNotifier:
    def post_teams_message(self, title, time, summary, commit_url, teams_webhook_url):
        message_data = {
            "@type": "MessageCard",
            "themeColor": "0076D7",
            "title": title,
            "text": str(time) + "\n\n" + str(summary),
            "potentialAction": [{
                "@type": "OpenUri",
                "name": "Go to commit page",
                "targets": [{"os": "default", "uri": commit_url}],
            }],
        }
        try:
            response = requests.post(teams_webhook_url, json=message_data)
            response.raise_for_status()
            logger.info("Post message to Teams successfully!")
            self.record_commit_history(message_data, status="success")
        except Exception as err:
            logger.error(f"An error occurred while sending message to Teams: {err}")
            self.record_commit_history(message_data, status="failed", error=str(err))

    def push_weekly_summary(self):
        self.clear_commit_history()
        logger.info("Pushing weekly summary report to Teams")
        weekly_commit_list = self.cosmosDB_client.get_weekly_commit(self.topic, self.language, self.root_commits_url, sort_order='DESC')
        summary_response = self.get_weekly_summary(weekly_commit_list)
        if summary_response:
            self.post_teams_message(self.generate_weekly_title(), summary_response, self.root_commits_url)

    def get_weekly_summary(self, commit_list):
        # Your existing logic for generating the weekly summary goes here
        pass

    def generate_weekly_title(self):
        last_monday = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday() + 7)
        last_sunday = last_monday + datetime.timedelta(days=6)
        return f"[Weekly Summary] {last_monday} ~ {last_sunday}"

    def record_commit_history(self, message_data, status, error=None):
        self.commit_history = {
            "teams_message_jsondata": message_data,
            "teams_message_webhook_url": self.teams_webhook_url,
            "commit_time": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "topic": self.topic,
            "root_commits_url": self.root_commits_url,
            "language": self.language,
            "get_weekly_summary_status": status
        }
        if error:
            self.commit_history["error"] = error

        if self.cosmosDB.save_commit_history_to_cosmosdb:
            success = self.cosmosDB_client.create_commit_history(self.commit_history)
            if success:
                logger.info("Create commit history in CosmosDB successfully!")
            else:
                logger.error("Create commit history in CosmosDB failed!")

    def clear_commit_history(self):
        self.commit_history.clear()
