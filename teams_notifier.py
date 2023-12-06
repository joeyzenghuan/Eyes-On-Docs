import requests
from logs import logger  

class TeamsNotifier:
    def post_teams_message(self, title, time, summary, teams_webhook_url, commit_url=None):
        if commit_url:
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
        else:
            message_data = {
                    "@type": "MessageCard",
                    "themeColor": "0076D7",
                    "title": title,
                    "text": str(summary),
                }
        try:
            response = requests.post(teams_webhook_url, json=message_data)
            response.raise_for_status()
            logger.info("Post message to Teams successfully!")
            return [message_data, "success", ""]
        except Exception as err:
            logger.error(f"An error occurred while sending message to Teams: {err}")
            return [message_data, "failed", str(err)]