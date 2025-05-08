# -*- coding: utf-8 -*-
from qg_botsdk import Model
from init import bot, guild, ResponseSplitter, ai # 导入 init 模块本身
import re
import threading

check_lock = threading.Lock()
query_lock = threading.Lock()

class Messager:
    def __init__(self, data: Model.MESSAGE):
        self.data = data
        self.guild_id = data.guild_id
        self.channel_id = data.channel_id

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

    def set_formal(self, member_id=None):
        # 如果没有提供 member_id，则默认为消息发送者
        if member_id is None:
            member_id = self.author_id
        bot.api.create_role_member(member_id, guild.id, guild.formal_id)

    def reply(self, msg):
        self.data.reply(self.head+msg,message_reference_id=self.data.id)

    def send(self, msg):
        self.data.reply(msg)

    def is_at(self):
        if '@小灵bot' in self.message:
            return True
        if 'mentions' not in self.data.__dict__:
            return False
        #print(f"message/bot_id = {guild.bot_id}")
        return any(item.id == guild.bot_id for item in self.data.mentions)

    def is_admin(self):
        return set(guild.admin_ids)&set(self.roles)
    
    def genshin(self):
        if '/深渊使用率' in self.message or '/角色持有' in self.message:
            self.reply('玩原神玩的')
            return True
        return False
    
    def set(self):
        if self.message!=' 过':
            return
        if not self.is_admin():
            self.reply('你不是管理员，没有使用该指令的权限')
            return
        members=''
        for member in self.data.mentions:
            self.set_formal(member.id)
            members+=f'<@{member.id}>'
        self.reply(f'已将{members}设置为正式成员\n{self.success}')

    def check(self):
        if self.channel_id != guild.assessment_id:
            return
        # 简化触发逻辑：始终检查是否在审核频道且足够长
        if len(self.message) < 50:
            if self.is_at():
                 self.reply('消息太短（<50字），小灵bot认为这不是一个委托表，不进行审核。')
            return

        # 通知用户审核已启动
        self.reply(('小灵bot收到委托表，正在思考ing\n'
                    '（若长时间未收到回复，可能是消息被tx拦截，请截图至人工审核区审核）'))

        try:
            if check_lock.acquire(blocking=False):
                try:
                    self.process(True)
                finally:
                    # 释放锁
                    check_lock.release()
            else:
                self.process(False)         
        except Exception as e:
            bot.logger.error(f"审核过程中发生错误 for {self.name}: {str(e)}")
            self.reply("抱歉，审核过程中发生内部错误，请稍后再试或联系管理员。")

    # 流式审核与处理逻辑
    def process(self, stream):
        bot.logger.info(f'{self.name} 发布委托表进行流式审核:\n{self.message}')
        stream = ai.check(self.message, True) # 调用流式 AI.check

        splitter = ResponseSplitter()
        final_tool_calls = {}
        content = "" #新增：用于累积最终内容

        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if hasattr(delta, 'reasoning_content'):
                reasoning_text = delta.reasoning_content
                if reasoning_text and stream: # 检查是否非空
                    for c in splitter.process(reasoning_text):
                        self.send(c)

            # 累积工具调用 (逻辑不变)
            for tool_call in chunk.choices[0].delta.tool_calls or []:
                index = tool_call.index
                if index not in final_tool_calls:
                    final_tool_calls[index] = tool_call
                final_tool_calls[index].function.arguments += tool_call.function.arguments

            # 修改：累积 content
            if delta.content:
                content += delta.content

        # 处理最终残留内容
        final_content = splitter.flush()
        if final_content and stream:
            self.send(final_content)

        if content:
            content = content.strip()
            if content != '':
                self.reply(content)

        print("Tools: ", final_tool_calls)
        for tool_call in  final_tool_calls.values():
            bot.logger.info(f"收到的工具调用信息 for {self.name}: {tool_call}")
            if tool_call.function.name == "set_formal":
                self.set_formal()
                self.reply(self.success)                    
                bot.logger.info(f'审核通过，执行 set_formal 工具 for {self.name}')

    def query(self):
        if self.channel_id!=guild.answer_id:
            return
        if not self.is_at():
            return
        with query_lock:  # 在 ai_query 方法中加锁
            self.reply('小灵bot收到问题，正在编写回复')
            bot.logger.info('开始答疑')
            reply=''
            splitter = ResponseSplitter() # 初始化分词器
            for chunk in ai.query(self.message):
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta.content:
                    for c in splitter.process(delta.content):
                        self.send(c) # 流式发送分词后的内容
                    reply+=delta.content # 累积完整回复用于日志记录
            # 处理分词器中剩余的内容
            final_content = splitter.flush()
            if final_content:
                self.send(final_content)
            bot.logger.info(reply)