# -*- coding: utf-8 -*-
from qg_botsdk import Model
from init import Guild, AI, bot, guild, bot_id, query_lock, ResponseSplitter, ToolCall, FunctionCall, ai # 导入全局 ai 实例
import re

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

    def set_formal(self):
        bot.api.create_role_member(self.author_id,guild.id,guild.formal_id)
    def reply(self, msg):
        self.data.reply(self.head+msg,message_reference_id=self.data.id)
    def send(self, msg):
        self.data.reply(msg)
    def is_at(self):
        if '@小灵bot' in self.message:
            return True
        if 'mentions' not in self.data.__dict__:
            return False
        return any(item.id == bot_id for item in self.data.mentions)

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
            # 或许可以添加检查，看是否是明确要求检查的 @ 消息？
            # 目前，除非明确 @ 机器人，否则忽略短消息
            if self.is_at():
                 self.reply('消息太短（<50字），小灵bot认为这不是一个委托表，不进行审核。')
            return

        # 通知用户检查已启动
        self.reply(('小灵bot收到委托表，正在思考ing\n'
                    '（若长时间未收到回复，可能是消息被tx拦截，请截图至人工审核区审核）'))

        try:
            # 调用执行 AI 检查并处理响应的内部方法
            self.ai_process()
        except Exception as e:
            bot.logger.error(f"审核过程中发生错误 for {self.name}: {str(e)}")
            self.reply("抱歉，审核过程中发生内部错误，请稍后再试或联系管理员。")

    # 核心审核与处理逻辑 (重命名以避免与主检查入口点混淆)
    def ai_process(self):
        bot.logger.info(f'{self.name} 发布委托表进行流式审核:\n{self.message}')
        stream = ai.check(self.message) # 调用流式 AI.check

        splitter = ResponseSplitter()
        final_tool_calls = {}
        content = "" # 新增：用于累积最终内容

        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if hasattr(delta, 'reasoning_content'):
                reasoning_text = delta.reasoning_content
                if reasoning_text: # 检查是否非空
                    for c in splitter.process(reasoning_text):
                        self.send(c)

            # 累积工具调用 (逻辑不变)
            if delta.tool_calls:
                for tool_call_chunk in delta.tool_calls:
                    index = tool_call_chunk.index
                    if index not in final_tool_calls:
                        # 如果是此索引的第一个块，则初始化工具调用结构
                        final_tool_calls[index] = ToolCall(
                            id=tool_call_chunk.id,
                            type='function',
                            function=FunctionCall(name=tool_call_chunk.function.name or "", arguments="")
                        )
                    # 追加参数块
                    if tool_call_chunk.function.arguments:
                         final_tool_calls[index].function.arguments += tool_call_chunk.function.arguments

            # 修改：累积 content
            if delta.content:
                content += delta.content

                # 处理最终残留内容
        final_content = splitter.flush()
        if final_content :
            self.send(final_content)

        # --- 流结束后处理 ---
        content_generated = False # 重置标记，仅当实际发送最终内容时为 True
        if content:
            content = content.strip()
            if content != '':
                self.reply(content)
                content_generated = True # 标记已生成并发送最终内容

        called_set_formal = False
        if final_tool_calls:
            bot.logger.info(f"收到的工具调用信息 for {self.name}: {final_tool_calls}")
            for index, tool_call in final_tool_calls.items():
                if tool_call.function.name == "set_formal":
                    bot.logger.info(f'审核通过，执行 set_formal 工具 for {self.name}')
                    try:
                        self.set_formal()
                        self.reply(self.success)
                        bot.logger.info(f' {self.name} 通过考核')
                        called_set_formal = True
                    except Exception as e:
                        bot.logger.error(f"执行 set_formal 时出错 for {self.name}: {e}", exc_info=True)
                        self.reply("执行通过审核操作时出错，请联系管理员。")

            if not called_set_formal:
                # 如果检测到工具调用但未包含 'set_formal'，则记录日志
                bot.logger.warning(f'收到工具调用但未包含 set_formal for {self.name}: {final_tool_calls}')
                # 决定此处是否需要回复 - 也许仅在未生成内容时？
                if not content_generated:
                    self.reply("审核响应包含意外的指令，请联系管理员。")

    def query(self):
        if self.channel_id!=guild.answer_id:
            return 
        if not self.is_at():
            return 
        with query_lock:  # 在 ai_query 方法中加锁
            self.reply('小灵bot收到问题，正在编写回复')
            bot.logger.info('开始答疑')
            reply=''
            for chunk in ai.query(self.message):
                self.data.reply(chunk)
                reply+=chunk
            bot.logger.info(reply)