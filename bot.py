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
import sys
# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from bot_config import *
from slack_sdk.models.blocks import SectionBlock, ActionsBlock, ButtonElement
# WebClient instantiates a client that can call API methods
# When using Bolt, you can use either `app.client` or the `client` passed to listeners.
client = WebClient(token=SLACK_TOKEN)
# logger = logging.getLogger(__name__)

#Accessing Piazza and loading data
piazza_id = "m0obli4e276tj" #TODO this is the suffix of the piazza url

p = Piazza()
p.user_login(email=piazza_email, password=piazza_password)
network = p.network(piazza_id)


#Accessing Slack and configuring the bot
channel="aiden-bot" #TODO Name of the channel to post to
last_seen_followups = {}
unresolved_posts = set()
#URL for posts on the page
POST_BASE_URL = "https://piazza.com/class/"+piazza_id+"?cid="
def get_max_id(feed):
    for post in feed:
        if "pin" not in post:
            return post["nr"]
    return -1
# def check_for_followup(network):
def check_for_new_posts(LAST_ID,network=network,include_link=True):
    while True:
        try:
            feed = network.get_feed(limit=100000)['feed'] # get a list of posts for this nedwork
            # Send New Post Notification
            UPDATED_LAST_ID = get_max_id(feed)
            
            if UPDATED_LAST_ID > LAST_ID:
                new_posts = [post for post in feed if post["nr"] > LAST_ID]
                for post in new_posts:
                    post_id = post["nr"]
                    unresolved_posts.add(post_id)
                    post_content = post['content_snipet']#network.get_post(post_id)['history'][0]['content']
                    attachment = None
                    message = None
                    if include_link is True:
                        blocks =[
                            {
                                "type": "header",
                                "text": {
                                    "type": "plain_text",
                                    "text": "New post!"
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Post:\n"+post_content
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"<{POST_BASE_URL}{post_id}|Click here to view post {post_id}.>"
                                }
                            },
                            {
                                "type": "actions",
                                "elements": [
                                    {
                                        "type": "button",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "Generate AIDEN Response!"
                                        },
                                        "style": "primary",
                                        "value": str(post_id),
                                    }
                                ]
                            }
                        ]
                        
                    else:
                        message="New post on Piazza!"
                    try:
                        result = client.chat_postMessage(
                            channel=channel,
                            text=message,
                            blocks=blocks  
                        )
                        # logger.info(result)

                    except SlackApiError as e:
                        print(f"Error posting message: {e}")
                LAST_ID = UPDATED_LAST_ID
            
            # #Send Follow-up Notification
            # for post in feed:
            #     post_id = post["nr"]
            #     #example post: {'fol': 'hw1|', 'm': 1726168643754, 'rq': 0, 'id': 'm0zo6tyerln7nn', 'my_post': True, 'log': [{'t': '2024-09-12T19:15:55Z', 'u': 'm0obm891qax1ib', 'n': 'create'}, {'t': '2024-09-12T19:17:23Z', 'u': 'm0obm891qax1ib', 'n': 'followup'}], 'unique_views': 1, 'score': 1.0, 'nid': 'm0obli4e276tj', 'is_new': False, 'version': 2, 'book': 1, 'bucket_name': 'Today', 'bucket_order': 3, 'folders': ['hw1'], 'nr': 41, 'main_version': 2, 'request_instructor': 0, 'subject': 'log test', 'no_answer_followup': 1, 'num_favorites': 0, 'type': 'question', 'tags': ['hw1', 'instructor-question', 'unanswered'], 'gd_f': 0, 'content_snipet': 'test', 'view_adjust': 0, 'no_answer': 1, 'modified': '2024-09-12T19:17:23Z', 'updated': '2024-09-12T19:15:55Z', 'status': 'active'}
            #     num_followups = sum(1 for entry in post['log'] if entry['n'] == 'followup')
            #     # print("Post ID: ", post_id, "Number of followups: ", num_followups)
            #     # print(post)
            #     # print()
            #     # num_followups = len(network.get_post(post_id)['children'])  
            #     if post_id not in last_seen_followups:
            #         last_seen_followups[post_id] = num_followups
            #     if num_followups > last_seen_followups[post_id]:
            #         last_seen_followups[post_id] = num_followups
            #         post_content = post['content_snipet']#network.get_post(post_id)['history'][0]['content']
            #         blocks =[
            #             {
            #                 "type": "header",
            #                 "text": {
            #                     "type": "plain_text",
            #                     "text": "New follow-up on post"+str(post_id)+"!"
            #                 }
            #             },
            #             {
            #                 "type": "section",
            #                 "text": {
            #                     "type": "plain_text",
            #                     "text": "Post:\n"+post_content
            #                 }
            #             },
            #             {
            #                 "type": "section",
            #                 "text": {
            #                     "type": "mrkdwn",
            #                     "text": f"<{POST_BASE_URL}{post_id}|Click here to view post {str(post_id)}.>"
            #                 }
            #             }
            #         ]
            #         try:
            #             result = client.chat_postMessage(
            #                 channel=channel,
            #                 text=None,
            #                 blocks=blocks  
            #             )
            #             # logger.info(result)

            #         except SlackApiError as e:
            #             print(f"Error posting message: {e}")
            #     # sleep(0.5)
            else:
                pass
            print("Slackbot is running...")
            sleep(10)
        except Exception as e:
            print("Error when attempting to get Piazza feed, going to sleep.... Error message: ", e)
            sleep(10)

if __name__ == '__main__':
    LAST_ID = get_max_id(network.get_feed()['feed'])
    check_for_new_posts(LAST_ID)