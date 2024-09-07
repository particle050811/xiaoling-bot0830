# -*- coding: utf-8 -*-
from qg_botsdk import BOT, Model
from openai import OpenAI
import os
import json
import base64
from datetime import datetime
import time
import re
import xml.etree.ElementTree as ET
import requests
import websocket
import threading

class AI:
    def __init__(self, name):
        self.model=root.find(f'{name}/model').text
        api_key=root.find(f'{name}/api_key').text
        base_url=root.find(f'{name}/base_url').text
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        with open('check_prompt.txt', 'r',encoding='utf-8') as file:
            self.check_prompt=file.read()
    def check(self, msg):
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": self.check_prompt
                },
                {
                    "role": "user",
                    "content": msg
                }
            ],
            response_format={
                'type': 'json_object'
            }
        )
        return response.choices[0].message.content
class BOT:
    def __init__(self) -> None:
        self.id = root.find('bot/id').text
        self.token = root.find('bot/token').text
    def start(self):
        websocket_url = 'wss://gateway-bot.fanbook.cn/websocket'
        requests_url='https://a1.fanbook.mobi/api/bot/'
        post_headers = {'Content-Type': 'application/json'}
        url = requests_url + f"{bot.token}/getMe"
        response = requests.get(url)
        data = response.json()

        if response.ok and data.get("ok"):
            user_token = data["result"]["user_token"]  #获取user token以建立连接
            device_id = "your_device_id"
            version_number = "1.6.60"
            #拼接base64字符串
            super_str = base64.b64encode(json.dumps({
                "platform": "bot",
                "version": version_number,
                "channel": "office",
                "device_id": device_id,
                "build_number": "1"
            }).encode('utf-8')).decode('utf-8')
            global ws_url
            ws_url = websocket_url + f"?id={user_token}&dId={device_id}&v={version_number}&x-super-properties={super_str}"  #准备url
            #websocket.enableTrace(True)
            global ws 
            ws = websocket.WebSocketApp(ws_url,
                                        on_message=on_message,
                                        on_error=on_error,
                                        on_close=on_close,
                                        on_open=on_open)
            ws.on_open = on_open
            ws.run_forever()
    def check(self,response):
        if response.status_code == 200:
            data = response.json()
            json_str = json.dumps(data, ensure_ascii=False ,indent=4)
            print(json_str)
        else:
            print(f'请求失败，状态码: {response.status_code}')
            print(response.text)    
    def get_channels(self):
        url = f'https://a1.fanbook.cn/api/bot/{bot.token}/channel/list'
        headers = {
            'Content-Type': 'application/json'
        }
        body = {
            "guild_id":guild.id
        }
        response = requests.post(url, headers=headers, data=json.dumps(body))
        #self.check(response)
        data = response.json()
        return data['result']    
    def send(self,content):
        #time.sleep(5)
        url = f'https://a1.fanbook.cn/api/bot/{bot.token}/sendMessage'
        headers = {
            'Content-Type': 'application/json'
        }
        body = {
            "chat_id":guild.assessment_id,
            "text":content
        }
        response = requests.post(url, headers=headers, data=json.dumps(body))
        self.check(response)
    
class Guild:
    def __init__(self,is_test:bool):
        if (is_test):
            self.id = root.find('guild_id/test').text
        else:
            self.id = root.find('guild_id/formal').text
    def set(self):
        self.channels=bot.get_channels()
        
        self.channel_dict = {channel['name']: channel['channel_id'] for channel in self.channels}
        self.assessment_id = self.channel_dict['ai审核区']
class Message:
    def __init__(self,data) -> None:
        self.content=data['desc']
        self.message_id=data['message_id']
        self.user_id=data['user_id']
        self.channel_id=data['channel_id']
        self.nickname=data['author']['nickname']
        
def on_message(ws, message):
    #print('收到消息')
    #print(message)
    data = json.loads(message)
    json_str = json.dumps(data, ensure_ascii=False ,indent=4)
    print(json_str)
    if data['action']=='push':
        forum_function(data['data'])
def on_error(ws, error):
    print("发生错误:" + str(error))
    reconnect()
def on_close(ws):
    print("连接已关闭")
    reconnect()
def on_open(ws):
    print("连接已建立")
    def run():
        while True:
            time.sleep(30)  # 每30秒发送一次Ping
            ws.send('{"type":"ping"}')
    threading.Thread(target=run).start()
def reconnect():
    time.sleep(5)  # 等待5秒后重连
    print('正在重连')
    ws = websocket.WebSocketApp(ws_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open)
    print('重连成功')
    ws.run_forever()
def forum_function(data):
    print('已开始处理消息')
    json_str = json.loads(data['content'])
    json_str = json.dumps(json_str, ensure_ascii=False ,indent=4)
    print(json_str)

tree = ET.parse('../fan-bot.xml')
root = tree.getroot()
deepseek = AI('deepseek')
bot = BOT()
guild = Guild(is_test=True)
bot.start()
guild.set()


