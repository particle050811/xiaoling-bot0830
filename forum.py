# -*- coding: utf-8 -*-
from qg_botsdk import Model
from init import Guild, bot, guild
import threading

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
        if self.is_legal():
            return
        self.remind()
        bot.logger.info(f'{self.user.user.username}非法发帖')

        if self.is_formal():
            self.reply((
                '机器人将在4分钟后把你在帖子广场的帖删除。'
                f'请在发帖选择<#{guild.cooperation_id}>板块，不要到帖子广场发帖。'
            ))
            threading.Timer(240, self.delete).start()
        else:
            self.reply((
                '机器人已自动将你在帖子广场的帖删除。'
                '由于很多人的举报信息收集表填写不完整，导致互助效率极度低下，'
                '故本频道需要通过考核后才能发帖。'
                '请先看公告，再来考核区参与考核。'
            ))
            self.delete()