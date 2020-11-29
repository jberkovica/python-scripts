import requests

def post_message_to_slack_channels(channel, url, jira, reason):

    payload = {
        "text": f"*[JIRA]* {jira} has problems\n ",
        "attachments": [
            {
                "title": f"{reason}",
                "text": f"<{url}/{jira}>",
                "mrkdwn_in": ["text"],
                "color": "danger",
                "footer": ":copyright: team name"}
        ]
    }

    requests.post(channel, json=payload)
