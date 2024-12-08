### 依赖安装

```shell bash
pip install openai
pip install qg-botsdk
```

### 配置文件要放在该文件夹同一个目录下

- code
  - xiaoling-bot0830
  - qq-bot.json


### 配置文件示例
```json
{
    "deepseek": {
      "model": "deepseek-chat",
      "api_key": "你的API-KEY",
      "base_url": "https://api.deepseek.com"
    },
    "qwen": {
      "model": "qwen-plus-1127",
      "api_key": "你的API-KEY",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    },
    "bot": {
      "bot_id": "你的QQ机器人botId",
      "bot_token": "你的QQ机器人botToken"
    },
    "test": "小灵bot测试频道 //你的测试频道名称",
    "formal": "学生互助频道 //你的正式频道名称",    
    "run_model": "qwen // 你选用的模型名称（qwen或deepseek或其他模型）",
    "run_guild": "test // 你选择运行的频道（test或者formal）"
}
```
