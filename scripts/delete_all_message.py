import json
import os
import time

import requests

HISTORY_URL = "https://slack.com/api/conversations.history"
DELMSG_URL = 'https://slack.com/api/chat.delete'
REPLIES_URL = "https://slack.com/api/conversations.replies" 
SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN")

def slack_delmsg(channel, ts):
    headers = {'Authorization': 'Bearer ' + SLACK_USER_TOKEN,
               'Content-Type': 'application/json; charset=utf-8'}
    payload = {'channel': channel, 'ts': ts}
    req = requests.post(DELMSG_URL, data=json.dumps(payload), headers=headers)
    print(req.text)

def slack_history(channel_id):
    header = {'Authorization': 'Bearer ' + SLACK_USER_TOKEN}
    payload  = {"channel" : "" + channel_id}
    res = requests.get(HISTORY_URL, headers=header, params=payload)
    json_data = res.json()
    messages = json_data["messages"]
    return messages

def slack_replies(channel_id, thread_id):
    header={'Authorization': 'Bearer ' + SLACK_USER_TOKEN}
    payload  = {"channel" : "" + channel_id, "ts" : "" + thread_id}
    res = requests.get(REPLIES_URL, headers=header, params=payload)
    json_data = res.json()
    messages = json_data["messages"]
    return messages

def main():
    # チャンネルIDをコンソールから入力
    channel_id = input("削除するチャンネルのIDを入力してください: ")
    
    mes_history = slack_history(channel_id)
    for i in mes_history:
        print(i["ts"])
        mes_replies = slack_replies(channel_id, i["ts"])
        for j in mes_replies:
            print("j_" + j["ts"])
            slack_delmsg(channel_id, j["ts"])
            time.sleep(0.5)
        slack_delmsg(channel_id, i["ts"])
        time.sleep(0.5)

if __name__ == "__main__":
    main()