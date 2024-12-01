# -*- coding: utf-8 -*-
from qg_botsdk import BOT, Model
from openai import OpenAI
import os
import json
from datetime import datetime
import time
import re
import xml.etree.ElementTree as ET
from codeshop.area import *

class AI:
    def __init__(self, name):
        self.model=root.find(f'{name}/model').text
        api_key=root.find(f'{name}/api_key').text
        base_url=root.find(f'{name}/base_url').text
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        with open('check_prompt.txt', 'r',encoding='utf-8') as file:
            self.check_prompt=file.read()
        with open('query_prompt.txt', 'r',encoding='utf-8') as file:
            self.query_prompt=file.read()        
    def check(self, msg):
        bot.logger.info('开始检验')
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.check_prompt},
                {"role": "user", "content": msg}
            ],
            #stream=True,
            response_format={'type': 'json_object'}
        )
        '''
        reply = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                reply += content
                print(content, end='', flush=True)
        print()
        '''
        return response.choices[0].message.content
    def query(self, msg):
        bot.logger.info('开始答疑')
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.query_prompt},
                {"role": "user", "content": msg}
            ]
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

        self.formal_id = self.role_dict['正式成员']
        self.smartboy_id = self.role_dict['违规发帖-请先看公告']

        self.log_id = self.channel_dict['机器人运行日志']
        self.assessment_id = self.channel_dict['AI自动审核区']
        self.cooperation_id = self.channel_dict['互助区']
        self.answer_id = self.channel_dict['答疑区']
        self.notice_id = self.channel_dict['公告区']
        #self.instant_id = self.channel_dict['即时互助区']
        
        return True

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
        self.success = (f'你通过了考核，请点击<#{guild.cooperation_id}>前往互助区发帖，主动私信联系别人互助。')
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
        
    def ai_check(self):
        bot.logger.info(self.name+'发布委托表：\n'+self.message)
        checked=ai.check(self.message)
        bot.logger.info('\n'+checked)
        #bot.logger.info(checked)
        #checked=re.sub(r'^```json|```$', '', checked, flags=re.MULTILINE)
        msg=json.loads(checked)
        if msg['委托表'] != '合法':
            return msg['委托表']
        reply = ''
        for value in msg.values():
            if value!='合法':
                reply += f'{value}\n'
        return reply[:-1]
    def ai_query(self):
        reply=ai.query(self.message)
        bot.logger.info(reply)
        return reply
    def check(self):
        #bot.logger.info('check')
        if self.channel_id!=guild.assessment_id:
            return False
        if not self.is_at():
            return False
        self.reply(('小灵bot已收到委托表,预计10s后会回复审核结果'
           '（没有这条消息说明你的消息违规，被tx拦截了，请截图后去人工区考核）'))
        reply=self.ai_check()
        if reply=='':
            self.reply(self.success)
            self.set_formal(self.author_id)
            bot.logger.info(f' {self.name} 通过考核')
        else:
            self.reply(reply)
        return True
    def query(self):
        if self.channel_id!=guild.answer_id:
            return False
        if not self.is_at():
            return False
        if "查区号" in self.message:
            reply=arname(self.message)
            self.reply(reply)
            return True
        if "查地方" in self.message:
            reply=arnum(self.message)
            self.reply(reply)
            return True
        self.reply('小灵bot收到问题，正在编写回复')
        reply=self.ai_query()
        self.reply(reply)
        return True

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
    def is_admin(self):
        return set(guild.admin_ids)&set(self.user.roles)
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
        """
        Checks if the forum post is legal and takes appropriate actions.

        If the post is not legal, it logs the event, reminds the user, and deletes the post if the user is not an admin.
        If the user is an admin, the post is not deleted but still logged.
        """
        if self.is_legal():
            return
        self.remind()
        bot.logger.info(f'{self.user.user.username}非法发帖')
        if self.is_admin():
            self.log(f'{self.user.user.username}非法发帖,但是权限较高，所以保留帖子内容')
            
        else:
            self.log(f'{self.user.user.username}非法发帖')
            self.delete()
        
        
        if self.is_formal():
            self.reply((
                '机器人已自动将你在帖子广场的帖删除。'
                f'请在发帖选择<#{guild.cooperation_id}>板块，不要到帖子广场发帖。'
            ))
        else:
            self.reply((
                '机器人已自动将你在帖子广场的帖删除。'
                '由于很多人的举报信息收集表填写不完整，导致互助效率极度低下，'
                '故本频道需要通过考核后才能发帖。'
                '请先看公告，再来考核区参与考核。'
            )) 

                                                                
        
        
tree = ET.parse('../qq-bot.xml')
root = tree.getroot()
botId = root.find('bot/id').text
botToken = root.find('bot/token').text
bot = BOT(bot_id=botId, bot_token=botToken, is_private=True)

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
    if user.query():
        return

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
    global ai; ai = AI('qwen-plus')
    global guild; guild = Guild(is_test=False)
    global bot_id; bot_id=bot.api.get_bot_info().data.id

if __name__ == "__main__":
    bot.start()