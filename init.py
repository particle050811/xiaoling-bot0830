# -*- coding: utf-8 -*-
from qg_botsdk import BOT, Model
from openai import OpenAI
from dataclasses import dataclass
import json

@dataclass
class FunctionCall:
    name: str
    arguments: str

@dataclass
class ToolCall:
    id: str
    type: str
    function: FunctionCall

# 定义全局的 set_formal tool
SET_FORMAL_TOOL = {
    "type": "function",
    "function": {
        "name": "set_formal",
        "description": "将用户设置为正式成员，当且仅当用户的委托表完全符合所有规范时调用。",
        "parameters": {
            "type": "object",
            "properties": {}, # 此工具不需要参数
            "required": []
        }
    }
}

class AI:
    def __init__(self):
        self.llm_check=cg[cg['llm_check']]
        self.llm_query=cg[cg['llm_query']]
        with open('check_prompt.txt', 'r',encoding='utf-8') as file:
            self.check_prompt=file.read()
        with open('query_prompt.txt', 'r',encoding='utf-8') as file:
            self.query_prompt=file.read()
            
    def check(self, msg, stream):
        bot.logger.info('开始检验')
        client = OpenAI(api_key=self.llm_check['api_key'],
                        base_url=self.llm_check['base_url'])

        response = client.chat.completions.create(
            model=self.llm_check['model'],
            messages=[
                {"role": "user", "content": self.check_prompt},
                {"role": "user", "content": msg}
            ],
            tools=[SET_FORMAL_TOOL], # 使用全局变量
            tool_choice="auto",  # 让模型自行决定是否调用函数
            stream=stream # 是否启用流式传输
        )
        return response

    def query(self, msg):
        client=OpenAI(api_key=self.llm_query['api_key'],
                      base_url=self.llm_query['base_url'])
        response = client.chat.completions.create(
            model=self.llm_query['model'],
            messages=[
                {"role": "user", "content": self.query_prompt},
                {"role": "user", "content": msg}
            ],
            stream=True
        )
        return response

class ResponseSplitter:
    def __init__(self):
        self.buffer = ''
        self.max_length = 100

    def process(self, new_content):
        self.buffer += new_content
        # 优先处理双换行
        dbl_newline = self.buffer.rfind('\n\n')
        if dbl_newline != -1:
            yield self.buffer[:dbl_newline]
            self.buffer = self.buffer[dbl_newline+2:]
            return

        # 处理单换行（仅在超过长度时）
        if len(self.buffer) < self.max_length:
            return
        single_newline = self.buffer.rfind('\n')
        if single_newline > self.max_length:
            yield self.buffer[:single_newline]
            self.buffer = self.buffer[single_newline+1:]
            return
        
        # 处理句号（仅在超过长度时）
        if len(self.buffer) < self.max_length + 30:
            return
        single_newline = max(self.buffer.rfind('。'),self.buffer.rfind('；'))
        if single_newline > self.max_length + 30:
            yield self.buffer[:single_newline+1]
            self.buffer = self.buffer[single_newline+1:]
            return

    def flush(self):
        content = self.buffer.strip()
        self.buffer = ''
        return content if content else None

class Guild:
    def __init__(self,name):
        self.name = name
        bot.logger.info(f'机器人在{self.name}运行')
        self.bot_id = None # 初始化 bot_id 实例属性
        self.id = ''

    def set(self,guild_id):
        if self.id != '':
            return True
        name=bot.api.get_guild_info(guild_id).data.name
        if (name != self.name):
            return False

        self.bot_id=bot.api.get_bot_info().data.id
        #print(f"init/bot_id = {self.bot_id}")
        self.id = guild_id
        self.channels = bot.api.get_guild_channels(self.id).data
        self.roles = bot.api.get_guild_roles(self.id).data.roles

        self.admin_ids = [sf.id for sf in self.roles if '管理' in sf.name]
        self.channel_dict = {channel.name: channel.id for channel in self.channels}
        self.role_dict = {sf.name: sf.id for sf in self.roles}

        self.formal_id = self.role_dict['正式成员']
        self.smartboy_id = self.role_dict['违规发帖-看公告-选择互助区发帖']

        #self.log_id = self.channel_dict['机器人运行日志']
        self.assessment_id = self.channel_dict['AI自动审核区']
        self.cooperation_id = self.channel_dict['互助区']
        self.answer_id = self.channel_dict['答疑区']
        self.notice_id = self.channel_dict['公告区']
        #self.instant_id = self.channel_dict['即时互助区']

        return True

# 全局变量初始化
with open('../qq-bot.json', 'r', encoding='utf-8') as file:
    cg = json.load(file)
bot = BOT(**cg['bot'], is_private=True)
ai = AI()
guild = Guild(cg[cg['run_guild']])
