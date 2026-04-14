# AIagentWeb 智能体网页问答系统

## 项目简介

AIagentWeb 是一个基于 Flask + 前端页面的本地智能体问答系统，集成了 Qwen3:0.6b 大语言模型，支持自然语言对话、时间日期查询、天气查询、A股股价查询、语音播报、邮件发送等多种实用功能。

---

## 目录结构

```
AIagentWeb/
│
├── app.py                  # 主后端接口入口
├── requirements.txt        # Python依赖包清单
├── README.md               # 项目说明文档
├── VOICE_FEATURES.md       # 语音功能说明
│
├── public/                 # 前端页面与静态资源
│   ├── index.html          # 主页面
│   ├── app.js              # 前端逻辑
│   └── styles.css          # 页面样式
│
├── resources/              # 资源文件夹（如模型、图片等）
│
├── time_query/             # 时间日期查询功能模块
│   └── time_query.py
│
├── weather_query/          # 天气查询功能模块
│   └── weather_query.py
│
├── voice_feature/          # 语音播报功能模块
│   └── voice_feature.py
│
├── stock_query/            # 股价查询功能模块
│   ├── stock_query.py
│   └── test_stock.py       # 股价查询测试脚本
│
├── mail_utils/             # 邮件发送功能模块
│   ├── __init__.py
│   └── email_tool.py
```

---

## 主要功能

- **自然语言对话**：集成 Qwen3:0.6b 本地大模型，支持多语言、上下文对话。
- **时间/日期/星期查询**：可回答“现在几点”“今天星期几”等问题。
- **天气查询**：支持全国主要城市天气、温度、空气质量等实时查询。
- **A股股价查询**：输入6位股票代码，实时获取中国A股行情（新浪财经接口）。
- **语音播报**：基于 edge-tts，支持多语种文本转语音。
- **邮件发送**：支持通过SMTP协议发送邮件，参数可自定义。

---

## 依赖环境

- Python 3.9+
- Flask >= 3.0.0
- requests >= 2.31.0
- edge-tts >= 7.2.7

安装依赖：
```
pip install -r requirements.txt
```

---

## 启动方式

1. 激活虚拟环境（如已配置）：
   ```
   & e:/Python/Package/my_venv/Scripts/Activate.ps1
   ```
2. 启动后端服务：
   ```
   python app.py
   ```
3. 访问 http://127.0.0.1:3000/ 查看网页端。

---

## API接口说明

- `/api/chat`：主对话接口，支持多轮对话和工具调用。
- `/api/tts`：文本转语音接口。
- `/api/tts-status`：语音服务状态检测。

---

## 工具能力说明

- `get_current_time(query_type)`：查询时间/日期/星期。
- `get_weather(city)`：查询天气。
- `get_stock_price_cn(ticker)`：查询A股实时股价。
- `send_email(...)`：发送邮件。

---

## 前端说明

- 页面入口：`public/index.html`
- 主要逻辑：`public/app.js`
- 支持语音播报、输入、结果展示等。

---

## 进阶说明

- 可扩展更多工具，只需在对应子模块添加功能并在 app.py 注册。
- 支持多语言和多种语音播报风格。
- 邮件发送需配置正确的SMTP服务器、端口、账号和授权码。

---

## 贡献与反馈

如有建议、Bug反馈或功能需求，欢迎提交 Issue 或 PR。

---

## License

MIT
