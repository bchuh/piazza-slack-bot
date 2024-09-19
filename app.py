from flask import Flask, request, jsonify
import datetime
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
from bot_config import *
from piazza_api import Piazza
import logging
import os
import warnings
from piazza_api.exceptions import AuthenticationError
warnings.filterwarnings("ignore", category=UserWarning, message="The top-level `text` argument is missing")

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

client = WebClient(token=SLACK_TOKEN)
piazza_id = "m0obli4e276tj" #TODO this is the suffix of the piazza url

p = Piazza()
p.user_login(email=piazza_email, password=piazza_password)
aiden_cookie = p._rpc_api.get_cookies()
network = p.network(piazza_id)



#URL for posts on the page
POST_BASE_URL = "https://piazza.com/class/"+piazza_id+"?cid="

logging.basicConfig(filename=os.path.join(os.getcwd(), "runtime.log"), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def log_post(log_type, post_id, post_content, time, response, slack_user_id, slack_user_name):
    """
    log_type: int, 0 for getting AIDEN response log, 1 for submitting modified response log
    """
    # logger = logging.getLogger(__name__)
    # logging.info(f"{log_type}, {post_id}, {post_content}, {time}, {response}, {slack_user_id}, {slack_user_name}")
    try:
        logging.info(f"{log_type}, {post_id}, {post_content}, {time}, {response}, {slack_user_id}, {slack_user_name}")
    except Exception as e:
        logging.error(f"Error logging post: {e}")

# @app.route('/llm/chat', methods=['POST'])
cred_dict = {}
@app.route('/slack/events', methods=['POST'])
def handle_interaction():
    if request.content_type == 'application/json':
        data = request.json
        # Respond to Slack's challenge verification
        if 'challenge' in data:
            return jsonify({'challenge': data['challenge']}), 200
    
        # Detect "list" message
        if 'event' in data:
            event = data['event']
            # example data {'token': 'm0ACjdyEXmWnOdv9NLXvw0zP', 'team_id': 'T07KWGN6W5T', 'context_team_id': 'T07KWGN6W5T', 'context_enterprise_id': None, 'api_app_id': 'A07KZA9D8SX', 'event': {'user': 'U07KZD7M6LS', 'type': 'message', 'ts': '1726253641.515229', 'client_msg_id': '9497fb8f-f3cd-4ad6-ba36-d488c81cc605', 'text': 'list', 'team': 'T07KWGN6W5T', 'blocks': [{'type': 'rich_text', 'block_id': '3nsCA', 'elements': [{'type': 'rich_text_section', 'elements': [{'type': 'text', 'text': 'list'}]}]}], 'channel': 'C07KSQ27X70', 'event_ts': '1726253641.515229', 'channel_type': 'channel'}, 'type': 'event_callback', 'event_id': 'Ev07LYU0B6CX', 'event_time': 1726253641, 'authorizations': [{'enterprise_id': None, 'team_id': 'T07KWGN6W5T', 'user_id': 'U07KZADLXFV', 'is_bot': True, 'is_enterprise_install': False}], 'is_ext_shared_channel': False, 'event_context': '4-eyJldCI6Im1lc3NhZ2UiLCJ0aWQiOiJUMDdLV0dONlc1VCIsImFpZCI6IkEwN0taQTlEOFNYIiwiY2lkIjoiQzA3S1NRMjdYNzAifQ'}
            if event.get('type') == 'message' and 'list' in event.get('text', '').lower():
                channel_id = event.get('channel')
                network = p.network(piazza_id)
                # Query Piazza for unresolved posts (posts with no instructor response)              
                unresolved_posts = [post for post in network.get_feed(limit=100000)['feed'] if 'no_answer' in post and post['no_answer'] == 1]
                
                # Format and send the response message
                blocks = []
                for post in unresolved_posts:
                    post_id = post['nr']
                    content_snippet = post['content_snipet']
                    #example post: {'fol': 'hw1|', 'm': 1725917597682, 'rq': 0, 'id': 'm0virxf6cox1am', 'log': [{'t': '2024-09-09T21:33:17Z', 'u': 'lezv0orf1gz65e', 'n': 'create'}], 'unique_views': 3, 'score': 3.0, 'nid': 'm0obli4e276tj', 'is_new': False, 'version': 1, 'bucket_name': 'Last week', 'bucket_order': 6, 'folders': ['hw1'], 'nr': 27, 'main_version': 1, 'request_instructor': 0, 'subject': 'test19', 'no_answer_followup': 0, 'num_favorites': 0, 'type': 'question', 'tags': ['hw1', 'instructor-question', 'unanswered'], 'gd_f': 0, 'content_snipet': 'Test post id', 'view_adjust': 0, 'no_answer': 1, 'modified': '2024-09-09T21:33:17Z', 'updated': '2024-09-09T21:33:17Z', 'status': 'active'}
                    title = post['subject']
                    
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "plain_text",
                                "text": f"Post {post_id}\nTitle: "+title+"\n"+content_snippet,
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
                    # Send a Slack message containing the unresolved posts
                    try:
                        client.chat_postMessage(
                            channel=channel_id,
                            blocks=blocks,
                            text=''
                        )
                    except SlackApiError as e:
                        print(f"Error posting message: {e}")

    else:
        payload = json.loads(request.form.get('payload'))
        payload_type = payload['type']
        post_id = payload['actions'][0]['value']
        # Detect Button Click
        if payload_type == 'block_actions':
            button_name = payload['actions'][0]['text']['text']
            #Extract Slack user info
            user_id = payload['user']['id']
            user_name = payload['user']['username']
            if button_name == "Generate AIDEN Response!":
                claim_time = datetime.datetime.now()


                #Extract post info
                post_id = payload['actions'][0]['value'] 
                network = p.network(piazza_id)
                post = network.get_post(post_id)
                # example post: {'history_size': 1, 'folders': ['hw1'], 'nr': 16, 'data': {'embed_links': []}, 'created': '2024-09-09T20:28:16Z', 'bucket_order': 3, 'no_answer_followup': 0, 'change_log': [{'anon': 'no', 'uid': 'lezv0orf1gz65e', 'data': 'm0vggb2k4ln6oj', 'v': 'all', 'type': 'create', 'when': '2024-09-09T20:28:16Z'}], 'bucket_name': 'Today', 'history': [{'anon': 'no', 'uid': 'lezv0orf1gz65e', 'subject': 'test8', 'created': '2024-09-09T20:28:16Z', 'content': 'test content of post'}], 'type': 'question', 'anon_map': {}, 'tags': ['hw1', 'instructor-question', 'unanswered'], '': [], 'unique_views': 2, 'children': [], 'tag_good_arr': [], 'no_answer': 1, 'anon_icons': True, 'id': 'm0vggb2evmf6oi', 'config': {'has_emails_sent': 1}, 'status': 'active', 'drafts': {}, 'request_instructor': 0, 'request_instructor_me': False, 'bookmarked': 1, 'num_favorites': 0, 'my_favorite': False, 'is_bookmarked': False, 'is_tag_good': False, 'q_edits': [], 'i_edits': [], 's_edits': [], 't': 1725913788302, 'default_anonymity': 'no'}
                content = post['history'][0]['content']
                title = post['history'][0]['subject']
                tags = post['tags']

                llm_input = "For semester fall 2024, regarding "+';'.join(tags)+", "+title+". "+content
                llm_response = "This is a placeholder response from LLM API"
                # client.chat_postMessage(channel=payload['channel']['id'], text=f"Post_id: {post_id}\nContent: {content}\nClaimed the question at {click_time}.\nLLM Response: {llm_response}")
                blocks = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "AIDEN Response for Post" + post_id +"!"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"<@{user_id}>"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "Title: "+title+"\n"+content
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
                        "type": "input",
                        "block_id": "content_input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "input_field",
                            "initial_value": llm_response
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "AIDEN response: (Verify and modify the content if needed)"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Submit to Piazza"
                                },
                                "style": "primary",
                                "value": str(post_id)
                            }
                        ]
                    }
                ]
                original_blocks = payload['message']['blocks']
                for block in original_blocks:
                    if block['type'] == 'actions':  # Find the actions block
                        for element in block['elements']:
                            if element['type'] == 'button' and element['value']==str(post_id):  # Check if it's a button
                                # Update the button text to show it was claimed by the user
                                element['text']['text'] = "Claimed by " + user_name + "!"
                result = client.chat_update(
                    channel=payload['channel']['id'],
                    ts=payload['container']['message_ts'],  # Timestamp of the original message
                    blocks=original_blocks  # Use the modified blocks
                )
                result = client.chat_postMessage(
                    channel=payload['channel']['id'],
                    thread_ts=payload['container']['message_ts'],  # The original message's timestamp
                    text=f"",
                    blocks=blocks  
                )
                log_post(0, post_id, content, claim_time, llm_response, user_id, user_name)
            elif button_name=="Submit to Piazza" and user_id not in cred_dict:
                #Get TA's login info before posting
                dm_response = client.conversations_open(users=user_id)
                dm_channel = dm_response['channel']['id']
                # Prompt for email and password in the DM
                blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "Please provide your Piazza login credentials to submit the response."
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "email_input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "email_field",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Enter your Piazza email"
                            }
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Piazza Email"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "password_input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "password_field",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Enter your Piazza password"
                            }
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Piazza Password"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Submit Piazza Credentials"
                                },
                                "style": "primary",
                                "value": str(post_id)  # Pass post_id for context
                            }
                        ]
                    }
                ]
                client.chat_postMessage(
                    channel=dm_channel,
                    blocks=blocks,
                    text="Please provide your Piazza login credentials."
                )
            elif button_name=="Submit to Piazza" and user_id in cred_dict:
                #Send the edited content to Piazza
                post_time = datetime.datetime.now()

                #Load TA's cookie
                TA_cookie = cred_dict[user_id]
                p._rpc_api.set_cookies(cookies=TA_cookie)
                network = p.network(piazza_id)

                #Update TA's cookie
                TA_cookie = p._rpc_api.get_cookies()
                cred_dict[user_id] = TA_cookie

                #Extract Slack user info
                user_id = payload['user']['id']
                user_name = payload['user']['username']

                #Extract post info
                post_id = payload['actions'][0]['value']
                post = network.get_post(post_id)
                content = post['history'][0]['content']
                title = post['history'][0]['subject']

                edited_content = payload['state']['values']['content_input']['input_field']['value']
                network.create_instructor_answer(network.get_post(post_id), edited_content, 0)
                
                #Set back to AIDEN's cookie
                p._rpc_api.set_cookies(cookies=aiden_cookie)
                try:
                    client.chat_update(
                        channel=payload['channel']['id'],
                        ts=payload['container']['message_ts'],  # This is the timestamp of the original message to be updated
                        text=" ",  # Update the message text
                        blocks=[
                            {
                                "type": "header",
                                "text": {
                                    "type": "plain_text",
                                    "text": "AIDEN Response for Post" + post_id +"!"
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Title: "+title+"\n"+content
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
                                "type": "input",
                                "block_id": "content_input",
                                "element": {
                                    "type": "plain_text_input",
                                    "action_id": "input_field",
                                    "initial_value": edited_content
                                },
                                "label": {
                                    "type": "plain_text",
                                    "text": "AIDEN response: (Verify and modify the content if needed)"
                                }
                            },
                            {
                                "type": "actions",
                                "elements": [
                                    {
                                        "type": "button",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "Submitted by " + user_name + "!"
                                        },
                                        "style": "primary",
                                        "value": str(post_id)
                                    }
                                ]
                            }
                        ]
                    )
                except SlackApiError as e:
                    logging.error(f"Error updating message: {e}")
                log_post(1, post_id, content, post_time, edited_content, user_id, user_name)
            elif button_name=="Submit Piazza Credentials":
                email = payload['state']['values']['email_input']['email_field']['value']
                password = payload['state']['values']['password_input']['password_field']['value']
                p_tmp = Piazza()
                try:
                    p_tmp.user_login(email=email, password=password)
                    network_tmp = p_tmp.network(piazza_id)
                    cookie_tmp = p_tmp._rpc_api.get_cookies()
                    cred_dict[user_id] = (cookie_tmp)
                    
                    client.chat_update(
                        channel=payload['container']['channel_id'],
                        ts=payload['container']['message_ts'],  # Update the original message
                        text="Credentials submitted successfully!"
                    )
                    # result = client.chat_update(
                    #     channel=payload['channel']['id'],
                    #     ts=payload['container']['message_ts'],  # Timestamp of the original message
                    #     blocks= [
                    #     {
                    #         "type": "section",
                    #         "text": {
                    #             "type": "plain_text",
                    #             "text": "Please provide your Piazza login credentials to submit the response."
                    #         }
                    #     },
                    #     {
                    #         "type": "input",
                    #         "block_id": "email_input",
                    #         "element": {
                    #             "type": "plain_text_input",
                    #             "action_id": "email_field",
                    #             "initial_value": "Email received!"
                    #         },
                    #         "label": {
                    #             "type": "plain_text",
                    #             "text": "Piazza Email"
                    #         }
                    #     },
                    #     {
                    #         "type": "input",
                    #         "block_id": "password_input",
                    #         "element": {
                    #             "type": "plain_text_input",
                    #             "action_id": "password_field",
                    #             "initial_value": "Password received!"
                    #         },
                    #         "label": {
                    #             "type": "plain_text",
                    #             "text": "Piazza Password"
                    #         }
                    #     },
                    #     {
                    #         "type": "actions",
                    #         "elements": [
                    #             {
                    #                 "type": "button",
                    #                 "text": {
                    #                     "type": "plain_text",
                    #                     "text": "Submitted Piazza Credentials!"
                    #                 },
                    #                 "style": "primary",
                    #                 "value": str(post_id)  # Pass post_id for context
                    #             }
                    #         ]
                    #     }
                    # ]
                    # )
                
                except AuthenticationError:
                    dm_response = client.conversations_open(users=user_id)
                    dm_channel = dm_response['channel']['id']
                    client.chat_postMessage(
                        channel=dm_channel,
                        text="Failed to authenticate your Piazza account. Please check your credentials and submit again."
                    )

        
        
            
            
    
    return '', 200

if __name__ == '__main__':
    app.run(port=3000)

# example payload: {'type': 'block_actions', 
# 'user': {'id': 'U07KZD7M6LS', 'username': 'hsuanlih', 'name': 'hsuanlih', 'team_id': 'T07KWGN6W5T'}, 
# 'api_app_id': 'A07KZA9D8SX', 'token': 'm0ACjdyEXmWnOdv9NLXvw0zP', 
# 'container': {'type': 'message', 'message_ts': '1725916138.337739', 'channel_id': 'C07KSQ27X70', 'is_ephemeral': False}, 
# 'trigger_id': '7702017900322.7676566234197.290accc0bd4fe7e21c18401a48c9ed5b', 
# 'team': {'id': 'T07KWGN6W5T', 'domain': 'aidenbot'}, 
# 'enterprise': None, 'is_enterprise_install': False, 
# 'channel': {'id': 'C07KSQ27X70', 'name': 'aiden-bot'}, 
# 'message': {'user': 'U07KZADLXFV', 'type': 'message', 'ts': '1725916138.337739', 'bot_id': 'B07KSQAML94', 'app_id': 'A07KZA9D8SX', 'text': 'AIDEN Response: Submit to Piazza 按钮，及互动元素', 'team': 'T07KWGN6W5T', 
#             'blocks': [
#                 {'type': 'section', 'block_id': 'l8UyJ', 'text': {'type': 'mrkdwn', 'text': 'AIDEN Response:', 'verbatim': False}}, 
#                 {'type': 'input', 'block_id': 'content_input', 'label': {'type': 'plain_text', 'text': 'Verify and modify the content if needed', 'emoji': True}, 'optional': False, 'dispatch_action': False, 'element': {'type': 'plain_text_input', 'action_id': 'input_field', 'initial_value': 'helloooo', 'dispatch_action_config': {'trigger_actions_on': ['on_enter_pressed']}}}, 
#                 {'type': 'actions', 'block_id': 'OTONs', 'elements': [{'type': 'button', 'action_id': 'iVUn6', 'text': {'type': 'plain_text', 'text': 'Submit to Piazza', 'emoji': True}, 'style': 'primary', 'value': 'submit_edited_content'}]}]
#             }, 
# 'state': {'values': {'content_input': {'input_field': {'type': 'plain_text_input', 'value': 'modify helloooo'}}}}, 
# 'response_url': 'https://hooks.slack.com/actions/T07KWGN6W5T/7699139436213/yFx0Bcp7YFEJwb8EOdOnb82J', 'actions': [{'action_id': 'iVUn6', 'block_id': 'OTONs', 'text': {'type': 'plain_text', 'text': 'Submit to Piazza', 'emoji': True}, 'value': 'submit_edited_content', 'style': 'primary', 'type': 'button', 'action_ts': '1725916148.732128'}]}