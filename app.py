from flask import Flask, request, jsonify
import datetime
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
from bot_config import *
from piazza_api import Piazza


app = Flask(__name__)

client = WebClient(token=SLACK_TOKEN)
piazza_id = "m0obli4e276tj" #TODO this is the suffix of the piazza url

p = Piazza()
p.user_login(email=piazza_email, password=piazza_password)
network = p.network(piazza_id)


@app.route('/slack/events', methods=['POST'])
def handle_interaction():
    payload = json.loads(request.form.get('payload'))
    payload_type = payload['type']
    if payload_type == 'block_actions':
        button_name = payload['actions'][0]['text']['text']
        if button_name == "Claim!":
            click_time = datetime.datetime.now()
            post_id = payload['actions'][0]['value'] 
            
            post = network.get_post(post_id)
            # example post: {'history_size': 1, 'folders': ['hw1'], 'nr': 16, 'data': {'embed_links': []}, 'created': '2024-09-09T20:28:16Z', 'bucket_order': 3, 'no_answer_followup': 0, 'change_log': [{'anon': 'no', 'uid': 'lezv0orf1gz65e', 'data': 'm0vggb2k4ln6oj', 'v': 'all', 'type': 'create', 'when': '2024-09-09T20:28:16Z'}], 'bucket_name': 'Today', 'history': [{'anon': 'no', 'uid': 'lezv0orf1gz65e', 'subject': 'test8', 'created': '2024-09-09T20:28:16Z', 'content': 'test content of post'}], 'type': 'question', 'anon_map': {}, 'tags': ['hw1', 'instructor-question', 'unanswered'], '': [], 'unique_views': 2, 'children': [], 'tag_good_arr': [], 'no_answer': 1, 'anon_icons': True, 'id': 'm0vggb2evmf6oi', 'config': {'has_emails_sent': 1}, 'status': 'active', 'drafts': {}, 'request_instructor': 0, 'request_instructor_me': False, 'bookmarked': 1, 'num_favorites': 0, 'my_favorite': False, 'is_bookmarked': False, 'is_tag_good': False, 'q_edits': [], 'i_edits': [], 's_edits': [], 't': 1725913788302, 'default_anonymity': 'no'}
            content = post['history'][0]['content']
            llm_response = "This is a placeholder response from LLM API"
            client.chat_postMessage(channel=payload['channel']['id'], text=f"Post_id: {post_id}\nContent: {content}\nClaimed the question at {click_time}.\nLLM Response: {llm_response}")
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Question: " + content
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
                        "text": "AIDEN response: Verify and modify the content if needed"
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
            result = client.chat_postMessage(
                        channel=payload['channel']['id'],
                        blocks=blocks  
                    )
        else:
            #get the edited content
            post_id = payload['actions'][0]['value']
            edited_content = payload['state']['values']['content_input']['input_field']['value']
            network.create_instructor_answer(network.get_post(post_id), edited_content, 0)
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