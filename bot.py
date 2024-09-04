"""
This is a simple Slackbot that will
check a Piazza page for new posts every 1 minute.
Every time a new post is observed a notification will
be sent out
"""

from piazza_api import Piazza

from time import sleep
import logging
import os
# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from bot_config import *
# WebClient instantiates a client that can call API methods
# When using Bolt, you can use either `app.client` or the `client` passed to listeners.
client = WebClient(token=SLACK_TOKEN)
logger = logging.getLogger(__name__)

#Accessing Piazza and loading data
piazza_id = "m0obli4e276tj" #TODO this is the suffix of the piazza url

p = Piazza()
p.user_login(email=piazza_email, password=piazza_password)
network = p.network(piazza_id)

#Accessing Slack and configuring the bot
channel="aiden-bot" #TODO Name of the channel to post to


#URL for posts on the page
POST_BASE_URL = "https://piazza.com/class/"+piazza_id+"?cid="

def get_max_id(feed):
    for post in feed:
        if "pin" not in post:
            return post["nr"]
    return -1

def check_for_new_posts(LAST_ID,network=network,include_link=True):
    while True:
        try:
            UPDATED_LAST_ID = get_max_id(network.get_feed()['feed'])
            if UPDATED_LAST_ID > LAST_ID:
                attachment = None
                message = None
                if include_link is True:
                    attachment = [
                        {
                            "fallback": "New post on Piazza!",
                            "title": "New post on Piazza!",
                            "title_link": POST_BASE_URL+str(UPDATED_LAST_ID),
                            "text": "Follow the link to view this post",
                            "color": "good"
                        }
                    ]
                else:
                    message="New post on Piazza!"
                try:
                    # Call the chat.postMessage method using the WebClient
                    result = client.chat_postMessage(
                        channel=channel,
                        text=message,
                        attachments = attachment
                    )
                    logger.info(result)

                except SlackApiError as e:
                    logger.error(f"Error posting message: {e}")
                # bot.chat_postMessage(channel,message, \
                # as_user=bot_name,parse='full',attachments=attachment)
                LAST_ID = UPDATED_LAST_ID
            else:
                pass
            print("Slackbot is running...")
            sleep(60)
        except:
            print("Error when attempting to get Piazza feed, going to sleep...")
            sleep(60)

if __name__ == '__main__':
    LAST_ID = get_max_id(network.get_feed()['feed'])
    check_for_new_posts(LAST_ID)