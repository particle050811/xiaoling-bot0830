# -*- coding: utf-8 -*-
from qg_botsdk import BOT, Model
from openai import OpenAI
import os
import json
from datetime import datetime
import time
import re
import xml.etree.ElementTree as ET

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
class Guild:
    def __init__(self,is_test:bool):
        if (is_test):
            self.name = root.find('guild_name/test').text
        else:
            self.name = root.find('guild_name/formal').text
        bot.logger.info(f'机器人在{self.name}运行')
        self.id=''
        
    def set(self,guild_id):
        if self.id!='':
            return True
        name=bot.api.get_guild_info(guild_id).data.name
        if (name!=self.name):
            return False
        self.id=guild_id
        self.channels = bot.api.get_guild_channels(self.id).data
        self.roles = bot.api.get_guild_roles(self.id).data.roles

        self.admin_ids = [sf.id for sf in self.roles if '管理' in sf.name]
        self.channel_dict = {channel.name: channel.id for channel in self.channels}
        self.role_dict = {sf.name: sf.id for sf in self.roles}

        #self.formal_id = self.role_dict['正式成员']
        self.smartboy_id = self.role_dict['违规发帖-请先看公告']

        self.log_id = self.channel_dict['机器人运行日志']
        #self.assessment_id = self.channel_dict['AI自动审核区']
        #self.cooperation_id = self.channel_dict['互助区']
        #self.instant_id = self.channel_dict['即时互助区']
        
        return True
'''
class Messager:
    def __init__(self,data: Model.MESSAGE):
        self.data=data
        self.guild_id=data.guild_id
        self.channel_id=data.channel_id

        self.author_id=data.author.id
        self.name=data.author.username
        #bot.logger.info(data)
        if 'content' in data.__dict__:
            self.message=re.sub(r'<@!\d+>', '', data.content)
        else:
            self.message=''
        self.roles=data.member.roles

        self.head=f'<@{self.author_id}>\n'
        self.success = (f'你通过了考核，可以去<#{guild.cooperation_id}>发帖找人互助了。'
                f'发帖时不选择分区会被机器人自动删除。'
                f'如果找不到人互助，可以去<#{guild.instant_id}>实时找人互助')
    def set_formal(self,id):
        bot.api.create_role_member(id,guild.id,guild.formal_id)
    def reply(self, msg):
        self.data.reply(self.head+msg,message_reference_id=self.data.id)
    def is_at(self):
        if '@小灵bot' in self.message:
            return True
        if 'mentions' not in self.data.__dict__:
            return False
        return any(item.id == bot_id for item in self.data.mentions) 

    def is_admin(self):
        return set(guild.admin_ids)&set(self.roles)
    def genshin(self):
        #bot.logger.info('genshin')
        if self.message==' /深渊使用率' or self.message==' /角色持有':
            self.reply('玩原神玩的')
            return True
        return False
    def set(self):
        #bot.logger.info('set')
        if self.message!=' 过':
            return False
        if not self.is_admin():
            self.reply('你不是管理员，没有使用该指令的权限')
            return False
        members=''
        for member in self.data.mentions:
            self.set_formal(member.id)
            members+=f'<@{member.id}>'
        self.reply(f'已将{members}设置为正式成员\n{self.success}')
        return True
        
    def ask_ai(self):
        checked=deepseek.check(self.message)
        bot.logger.info(checked)
        msg=json.loads(checked)
        if msg['委托表'] != '合法':
            return msg['委托表']
        reply = ''
        for value in msg.values():
            if value!='合法':
                reply += f'{value}\n'
        return reply[:-1]
    def check(self):
        #bot.logger.info('check')
        if self.channel_id!=guild.assessment_id:
            return
        if not self.is_at():
            return
        self.reply(('小灵bot已收到委托表,预计10s后会回复审核结果'
           '（没有这条消息说明你的消息违规，被tx拦截了，请截图后去人工区考核）'
           f'以下为考核表原文：\n\n{self.message}'))
        reply=self.ask_ai()
        if reply=='':
            self.reply(self.success)
            self.set_formal(self.author_id)
            bot.logger.info(f' {self.name} 通过考核')
        else:
            self.reply(reply)    
''' 
class Forumer:
    def __init__(self,data: Model.FORUMS_EVENT):
        self.author_id=data.author_id
        self.thread_id=data.thread_info.thread_id
        self.channel_id=data.channel_id
        self.user=bot.api.get_member_info(data.guild_id,data.author_id).data

        self.head=f'<@{self.author_id}>\n'

    def reply(self,msg:str):
        bot.api.send_msg(channel_id=guild.assessment_id,
                         content=self.head+msg,
                         message_id=self.thread_id)
    def is_legal(self):
        for channel in guild.channels:
            if channel.name=='帖子广场' and channel.id==self.channel_id:
                return False
        return True
    def is_formal(self):
        return guild.formal_id in self.user.roles
    def delete(self):
        bot.api.delete_thread(self.channel_id,self.thread_id)
    def remind(self):
        bot.api.create_role_member(self.author_id,guild.id,guild.smartboy_id)
        bot.api.delete_role_member(self.author_id,guild.id,guild.smartboy_id)
    def log(self,content):
        bot.api.send_msg(channel_id=guild.log_id,
                         content=content,
                         message_id=self.thread_id)
    def check(self):
        if self.is_legal():
            return
        self.delete()
        self.remind()
        bot.logger.info(f'{self.user.user.username}非法发帖')
        self.log(f'{self.user.user.username}非法发帖')
        '''
        if self.is_formal():
            self.reply((
                '机器人已自动将你在帖子广场的帖删除。'
                f'请在发帖选择<#{guild.cooperation_id}>板块，不要到帖子广场发帖。'
                f'如果需要找人互助，可以去<#{guild.instant_id}>挂着，实时找人互助'
            ))
        else:
            self.reply((
                '机器人已自动将你在帖子广场的帖删除。'
                '由于很多人的举报信息收集表填写不完整，导致互助效率极度低下，'
                '故本频道需要通过考核后才能发帖。'
                '请先看公告，再来考核区参与考核。'
            ))
        '''
tree = ET.parse('../config.xml')
root = tree.getroot()
botId = root.find('bot/id').text
botToken = root.find('bot/token').text
bot = BOT(bot_id=botId, bot_token=botToken, is_private=True)
'''
@bot.bind_msg()
def deliver(data: Model.MESSAGE):
    if not guild.set(data.guild_id):
        return 
    if data.guild_id!=guild.id:
        return
    #bot.logger.info('permitted channel')
    user=Messager(data)
    if user.genshin():
        return
    if user.set():
        return
    if user.check():
        return
''' 
@bot.bind_forum()
def forum_function(data: Model.FORUMS_EVENT):
    if data.t != 'FORUM_THREAD_CREATE':
        return
    if not guild.set(data.guild_id):
        return 
    if data.guild_id!=guild.id:
        return
    user=Forumer(data)
    user.check()

@bot.register_start_event()
def init():
    global deepseek; deepseek = AI('deepseek')
    global guild; guild = Guild(is_test=False)
    global bot_id; bot_id=bot.api.get_bot_info().data.id

if __name__ == "__main__":
    bot.start()