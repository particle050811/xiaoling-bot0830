# -*- coding: utf-8 -*-
from init import bot, guild
from message import Messager
from forum import Forumer
from qg_botsdk import Model

@bot.bind_msg()
def deliver(data: Model.MESSAGE):
    if not guild.set(data.guild_id):
        return 
    if data.guild_id!=guild.id:
        return
    msg=Messager(data)

    if msg.genshin():
        return
    msg.set()
    msg.check()
    msg.query()

@bot.bind_forum()
def forum_function(data: Model.FORUMS_EVENT):
     if data.t != 'FORUM_THREAD_CREATE':
         return
     if not guild.set(data.guild_id):
         return 
     if data.guild_id!=guild.id:
         return
     #user=Forumer(data)
     #user.check()

if __name__ == "__main__":
    bot.start()
