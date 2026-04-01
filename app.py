from __future__ import annotations

import asyncio
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import edge_tts
import requests
from flask import Flask, Response, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
RESOURCES_DIR = BASE_DIR / "resources"


def load_env_files() -> None:
    for filename in (".env", ".env.local"):
        env_path = BASE_DIR / filename
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


load_env_files()

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "3000"))
EDGE_TTS_RATE = os.environ.get("EDGE_TTS_RATE", "+0%")
EDGE_TTS_VOLUME = os.environ.get("EDGE_TTS_VOLUME", "+0%")
EDGE_TTS_PITCH = os.environ.get("EDGE_TTS_PITCH", "+0Hz")

LANGUAGE_PROMPTS: Dict[str, str] = {
    "zh-CN": "你是一个自然、亲切、聪明的中文数字人助手。默认使用简体中文普通话口吻回答，表达口语化、简洁、有陪伴感。",
    "zh-HK": "你是一个自然、亲切、聪明的中文数字人助手。請盡量用粵語口吻回答，保持自然、易懂、友好。",
    "zh-TW": "你是一個自然、親切、聰明的繁體中文數字人助手。使用臺灣國語口吻回答，口語化、簡潔、有親和力。",
    "en-US": "You are a natural, friendly, and intelligent AI digital assistant. Respond in American English with a warm and conversational tone.",
    "en-GB": "You are a natural, friendly, and intelligent AI digital assistant. Respond in British English with a refined and warm tone.",
    "en-AU": "You are a natural, friendly, and intelligent AI digital assistant. Respond in Australian English with a cheerful and relaxed tone.",
    "ja-JP": "あなたは自然で、親切で、聡明なAIデジタルアシスタントです。自然な日本語で、やわらかく会話的な口調で回答してください。",
    "ko-KR": "당신은 자연스럽고 친절하며 똑똑한 AI 디지털 어시스턴트입니다. 자연스러운 한국어로 친절하게 답변해 주세요.",
    "fr-FR": "Vous êtes un assistant numérique IA naturel, bienveillant et intelligent. Répondez en français avec un ton chaleureux et conversationnel.",
    "de-DE": "Sie sind ein natürlicher, freundlicher und intelligenter KI-Digitalassistent. Antworten Sie auf Deutsch mit einem warmen und Gesprächston.",
    "es-ES": "Eres un asistente digital de IA natural, amigable e inteligente. Responde en español con un tono cálido y conversacional.",
    "pt-BR": "Você é um assistente digital de IA natural, amigável e inteligente. Responda em português brasileiro com um tom caloroso e conversacional.",
    "it-IT": "Sei un assistente digitale AI naturale, amichevole e intelligente. Rispondi in italiano con un tono caldo e conversazionale.",
    "ru-RU": "Вы естественный, дружелюбный и умный цифровой помощник ИИ. Отвечайте на русском языке с теплым и разговорным тоном.",
}

LANGUAGE_TTS_VOICES: Dict[str, str] = {
    "zh-CN": os.environ.get("EDGE_VOICE_ZH_CN", "zh-CN-XiaoxiaoNeural"),
    "zh-HK": os.environ.get("EDGE_VOICE_ZH_HK", "zh-HK-HiuGaaiNeural"),
    "zh-TW": os.environ.get("EDGE_VOICE_ZH_TW", "zh-TW-HsiaoYuNeural"),
    "en-US": os.environ.get("EDGE_VOICE_EN_US", "en-US-JennyNeural"),
    "en-GB": os.environ.get("EDGE_VOICE_EN_GB", "en-GB-SoniaNeural"),
    "en-AU": os.environ.get("EDGE_VOICE_EN_AU", "en-AU-NatashaNeural"),
    "ja-JP": os.environ.get("EDGE_VOICE_JA_JP", "ja-JP-NanamiNeural"),
    "ko-KR": os.environ.get("EDGE_VOICE_KO_KR", "ko-KR-SunHiNeural"),
    "fr-FR": os.environ.get("EDGE_VOICE_FR_FR", "fr-FR-DeniseNeural"),
    "de-DE": os.environ.get("EDGE_VOICE_DE_DE", "de-DE-KatjaNeural"),
    "es-ES": os.environ.get("EDGE_VOICE_ES_ES", "es-ES-ElviraNeural"),
    "pt-BR": os.environ.get("EDGE_VOICE_PT_BR", "pt-BR-FranciscaNeural"),
    "it-IT": os.environ.get("EDGE_VOICE_IT_IT", "it-IT-ElsaNeural"),
    "ru-RU": os.environ.get("EDGE_VOICE_RU_RU", "ru-RU-SvetlanaNeural"),
}

TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前时间、日期或星期几。当用户询问时间相关问题时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "enum": ["time", "date", "weekday", "full"],
                        "description": "查询类型：time-时间，date-日期，weekday-星期几，full-完整信息",
                    }
                },
                "required": ["query_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息，包括温度、天气状况、空气质量等。当用户询问天气相关问题时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'广州'、'北京'、'上海'等",
                    }
                },
                "required": ["city"],
            },
        },
    }
]

TOOLS_DESCRIPTION = """
你可以使用以下工具来帮助用户：

1. get_current_time(query_type) - 获取当前时间信息
   - query_type: "time" (时间), "date" (日期), "weekday" (星期几), "full" (完整信息)
   - 当用户询问"现在几点了"、"今天星期几"、"今天的日期"等问题时，请调用此工具

2. get_weather(city) - 获取指定城市的天气信息
   - city: 城市名称（如"广州"、"北京"、"上海"等）
   - 当用户询问"广州今天天气如何"、"北京今天多少度"、"上海天气怎么样"等问题时，请调用此工具

重要：当你需要使用工具时，请在思考过程中调用工具，然后基于工具返回的结果给用户一个自然、流畅的回答。
不要直接把工具调用的格式（如 JSON）展示给用户，而是要将工具的结果转化为你自己的话术来回答。

示例：
- 用户问："今天星期几？"
  你应该：调用 get_current_time 工具获取星期信息，然后回答"今天是星期三哦~"
  
- 用户问："广州天气怎么样？"
  你应该：调用 get_weather 工具获取天气信息，然后回答"广州今天多云，气温 19 到 27 度，北风 2 级，空气质量优。"
"""

app = Flask(__name__, static_folder=None)
TTS_STATUS_CACHE: Dict[str, Tuple[float, bool, str]] = {}
TTS_STATUS_TTL_SECONDS = 300


def strip_think_tags(text: str) -> str:
    return re.sub(
        r"<think>[\s\S]*?</think>", "", str(text or ""), flags=re.IGNORECASE
    ).strip()


def get_current_time(query_type: str) -> Dict[str, str]:
    """获取当前时间信息"""
    now = datetime.now()
    
    if query_type == "time":
        return {
            "time": now.strftime("%H:%M:%S"),
            "response": f"现在的时间是 {now.strftime('%H 点 %M 分 %S 秒')}。",
        }
    elif query_type == "date":
        return {
            "date": now.strftime("%Y-%m-%d"),
            "response": f"今天的日期是 {now.strftime('%Y 年 %m 月 %d 日')}。",
        }
    elif query_type == "weekday":
        weekday_map = {
            0: "星期一",
            1: "星期二",
            2: "星期三",
            3: "星期四",
            4: "星期五",
            5: "星期六",
            6: "星期日",
        }
        weekday = weekday_map[now.weekday()]
        return {
            "weekday": weekday,
            "response": f"今天是{weekday}。",
        }
    else:  # full
        weekday_map = {
            0: "星期一",
            1: "星期二",
            2: "星期三",
            3: "星期四",
            4: "星期五",
            5: "星期六",
            6: "星期日",
        }
        weekday = weekday_map[now.weekday()]
        return {
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "weekday": weekday,
            "response": f"现在是 {now.strftime('%Y 年 %m 月 %d 日')} {weekday} {now.strftime('%H 点 %M 分')}",
        }


CITY_CODES: Dict[str, str] = {
    "北京": "101010100",
    "北京市": "101010100",
    "广州": "101280101",
    "广州市": "101280101",
    "上海": "101020100",
    "上海市": "101020100",
    "深圳": "101280601",
    "深圳市": "101280601",
    "杭州": "101210101",
    "杭州市": "101210101",
    "南京": "101190101",
    "南京市": "101190101",
    "成都": "101270101",
    "成都市": "101270101",
    "武汉": "101200101",
    "武汉市": "101200101",
    "西安": "101110101",
    "西安市": "101110101",
    "重庆": "101040100",
    "重庆市": "101040100",
    "天津": "101030100",
    "天津市": "101030100",
    "苏州": "101190501",
    "苏州市": "101190501",
    "郑州": "101180101",
    "郑州市": "101180101",
    "长沙": "101250101",
    "长沙市": "101250101",
    "厦门": "101230201",
    "厦门市": "101230201",
    "青岛": "101120201",
    "青岛市": "101120201",
    "大连": "101070201",
    "大连市": "101070201",
    "沈阳": "101070101",
    "沈阳市": "101070101",
    "哈尔滨": "101050101",
    "哈尔滨市": "101050101",
    "长春": "101060101",
    "长春市": "101060101",
    "济南": "101120101",
    "济南市": "101120101",
    "合肥": "101220101",
    "合肥市": "101220101",
    "福州": "101220201",
    "福州市": "101220201",
    "南昌": "101240101",
    "南昌市": "101240101",
    "南宁": "101300101",
    "南宁市": "101300101",
    "贵阳": "101260101",
    "贵阳市": "101260101",
    "昆明": "101290101",
    "昆明市": "101290101",
    "拉萨": "101281401",
    "拉萨市": "101281401",
    "太原": "101100101",
    "太原市": "101100101",
    "石家庄": "101090101",
    "石家庄市": "101090101",
    "呼和浩特": "101080101",
    "呼和浩特市": "101080101",
    "银川": "101150101",
    "银川市": "101150101",
    "西宁": "101150201",
    "西宁市": "101150201",
    "乌鲁木齐": "101130101",
    "乌鲁木齐市": "101130101",
    "海口": "101310101",
    "海口市": "101310101",
    "三亚": "101310201",
    "三亚市": "101310201",
}


def get_city_code(city_name: str) -> Optional[str]:
    """获取城市代码"""
    city_name = city_name.strip()
    if city_name in CITY_CODES:
        return CITY_CODES[city_name]
    
    for city, code in CITY_CODES.items():
        if city_name in city or city in city_name:
            return code
    
    return None


def get_weather(city: str) -> Dict[str, Any]:
    """获取指定城市的天气信息"""
    city_code = get_city_code(city)
    if not city_code:
        return {
            "success": False,
            "response": f"抱歉，暂时无法查询'{city}'的天气信息，请尝试其他城市。",
        }
    
    try:
        url = f"http://t.weather.sojson.com/api/weather/city/{city_code}"
        response = requests.get(url, timeout=10)
        
        if not response.ok or response.status_code != 200:
            return {
                "success": False,
                "response": f"抱歉，获取{city}天气信息失败。",
            }
        
        data = response.json()
        
        if data.get("status") != 200:
            return {
                "success": False,
                "response": f"抱歉，获取{city}天气信息失败。",
            }
        
        city_info = data.get("cityInfo", {})
        weather_data = data.get("data", {})
        forecast = weather_data.get("forecast", [])
        
        if not forecast:
            return {
                "success": False,
                "response": f"抱歉，{city}的天气数据暂时不可用。",
            }
        
        today = forecast[0]
        
        city_name = city_info.get("city", city)
        weather_type = today.get("type", "未知")
        high_temp = today.get("high", "").replace("高温 ", "").replace("℃", "")
        low_temp = today.get("low", "").replace("低温 ", "").replace("℃", "")
        wind_dir = today.get("fx", "未知")
        wind_level = today.get("fl", "未知")
        humidity = weather_data.get("shidu", "未知")
        air_quality = weather_data.get("quality", "未知")
        pm25 = weather_data.get("pm25", "未知")
        notice = today.get("notice", "")
        
        response_text = (
            f"{city_name}今天{weather_type}，"
            f"气温{low_temp}~{high_temp}℃，"
            f"{wind_dir}{wind_level}，"
            f"湿度{humidity}，"
            f"空气质量{air_quality}"
        )
        
        if pm25 != "未知":
            response_text += f"，PM2.5 指数{pm25}"
        
        if notice:
            response_text += f"。{notice}"
        else:
            response_text += "。"
        
        return {
            "success": True,
            "city": city_name,
            "weather_type": weather_type,
            "high_temp": high_temp,
            "low_temp": low_temp,
            "wind_dir": wind_dir,
            "wind_level": wind_level,
            "humidity": humidity,
            "air_quality": air_quality,
            "pm25": pm25,
            "response": response_text,
        }
        
    except requests.RequestException:
        app.logger.exception("Failed to fetch weather for %s", city)
        return {
            "success": False,
            "response": f"抱歉，网络异常，无法获取{city}的天气信息。",
        }
    except Exception:
        app.logger.exception("Unexpected error fetching weather for %s", city)
        return {
            "success": False,
            "response": f"抱歉，查询{city}天气时发生错误。",
        }


def parse_tool_call(think_content: str) -> Optional[Dict[str, Any]]:
    """解析 <think> 标签中的工具调用"""
    if not think_content:
        return None
        
    match = re.search(r"<think>\s*({[\s\S]*?})\s*</think>", think_content, re.IGNORECASE)
    if not match:
        # 尝试直接匹配 JSON 格式
        match = re.search(r"{\s*\"name\"\s*:\s*\"(\w+)\"[\s\S]*?}", think_content)
        if not match:
            return None
    
    try:
        # 如果是第一种匹配方式，提取 JSON 部分
        if match.group(1):
            tool_data = json.loads(match.group(1))
        else:
            tool_data = json.loads(match.group(0))
        
        tool_name = tool_data.get("name")
        if tool_name in ["get_current_time", "get_weather"]:
            return tool_data
    except json.JSONDecodeError:
        return None
    
    return None


def execute_tool(tool_data: Dict[str, Any]) -> Optional[str]:
    """执行工具调用并返回结果"""
    tool_name = tool_data.get("name")
    arguments = tool_data.get("arguments", {})
    
    if tool_name == "get_current_time":
        query_type = arguments.get("query_type", "full")
        result = get_current_time(query_type)
        return result.get("response")
    elif tool_name == "get_weather":
        city = arguments.get("city", "")
        if not city:
            return "抱歉，请提供要查询的城市名称。"
        result = get_weather(city)
        return result.get("response")
    
    return None


async def synthesize_speech(text: str, voice: str) -> bytes:
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=EDGE_TTS_RATE,
        volume=EDGE_TTS_VOLUME,
        pitch=EDGE_TTS_PITCH,
    )
    chunks: List[bytes] = []
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks)


def check_tts_ready(language: str) -> Tuple[bool, str]:
    voice = LANGUAGE_TTS_VOICES.get(language, LANGUAGE_TTS_VOICES["zh-CN"])
    cached = TTS_STATUS_CACHE.get(voice)
    now = time.monotonic()
    if cached and now - cached[0] < TTS_STATUS_TTL_SECONDS:
        return cached[1], cached[2]

    try:
        audio = asyncio.run(synthesize_speech("test", voice))
        ready = bool(audio)
        message = "Edge-TTS 可用" if ready else "Edge-TTS 未返回音频数据"
    except Exception:
        app.logger.exception("Edge-TTS probe failed for voice %s", voice)
        ready = False
        message = "Edge-TTS 当前不可用"

    TTS_STATUS_CACHE[voice] = (now, ready, message)
    return ready, message


@app.post("/api/chat")
def api_chat() -> Response:
    try:
        body = request.get_json(silent=True) or {}
        model = body.get("model") or "qwen3:0.6b"
        language = body.get("language") or "zh-CN"
        messages = (
            body.get("messages") if isinstance(body.get("messages"), list) else []
        )

        system_prompt = (
            f"{LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS['zh-CN'])}\n"
            '你现在以"本地智能聊天数字人"的身份与用户对话。要求：\n'
            "1. 回答自然，不要机械列条目，除非用户明确需要。\n"
            "2. 默认简洁，适当体现情绪和陪伴感。\n"
            "3. 如果用户在做口语聊天，就像真人一样接话。\n"
            "4. 当用户询问时间、日期、星期几、天气等问题时，请使用工具来获取准确信息，然后将结果用自然的口吻告诉用户。\n"
            "5. 不要将工具调用的原始格式（如 JSON）直接展示给用户。\n"
            f"{TOOLS_DESCRIPTION}"
        )

        payload = {
            "model": model,
            "stream": False,
            "think": True,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "options": {"temperature": 0.8, "top_p": 0.9},
        }

        try:
            ollama_response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        except requests.RequestException:
            app.logger.exception("Failed to reach Ollama at %s", OLLAMA_URL)
            return (
                jsonify(
                    {
                        "error": "OLLAMA_UNAVAILABLE",
                        "message": "无法连接到 Ollama 服务。",
                    }
                ),
                502,
            )

        if not ollama_response.ok:
            return jsonify(
                {
                    "error": "OLLAMA_ERROR",
                    "message": ollama_response.text or "Ollama request failed.",
                }
            ), 502

        try:
            data = ollama_response.json()
        except ValueError:
            app.logger.exception("Ollama returned non-JSON response")
            return (
                jsonify(
                    {
                        "error": "OLLAMA_BAD_RESPONSE",
                        "message": "Ollama 返回了无法解析的数据。",
                    }
                ),
                502,
            )

        message_content = data.get("message", {}).get("content", "")
        think_content = data.get("message", {}).get("think", "")
        
        # 优先从 think_content 中解析工具调用，如果没有则检查 message_content
        tool_call = parse_tool_call(think_content)
        if not tool_call:
            tool_call = parse_tool_call(message_content)
        
        if tool_call:
            tool_result = execute_tool(tool_call)
            if tool_result:
                # 将工具结果整合到自然语言回答中
                final_message = f"{tool_result}"
                return jsonify(
                    {
                        "message": final_message,
                        "model": data.get("model") or model,
                        "tool_used": True,
                    }
                )
        
        # 如果没有工具调用，返回原始消息（去除 think 标签）
        return jsonify(
            {
                "message": strip_think_tags(message_content),
                "model": data.get("model") or model,
            }
        )
    except Exception:
        app.logger.exception("Unexpected server error in /api/chat")
        return jsonify({"error": "SERVER_ERROR", "message": "服务暂时不可用。"}), 500


@app.post("/api/tts")
def api_tts() -> Response:
    try:
        body = request.get_json(silent=True) or {}
        text = str(body.get("text") or "").strip()
        language = body.get("language") or "zh-CN"
        if not text:
            return jsonify({"error": "EMPTY_TEXT", "message": "text is required"}), 400

        voice = LANGUAGE_TTS_VOICES.get(language, LANGUAGE_TTS_VOICES["zh-CN"])
        audio_bytes = asyncio.run(synthesize_speech(text, voice))
        return Response(
            audio_bytes, mimetype="audio/mpeg", headers={"Cache-Control": "no-store"}
        )
    except Exception:
        app.logger.exception("TTS request failed")
        return (
            jsonify(
                {
                    "error": "TTS_UPSTREAM_ERROR",
                    "message": "语音服务当前不可用。",
                }
            ),
            502,
        )


@app.get("/api/tts-status")
def api_tts_status() -> Response:
    language = request.args.get("language") or "zh-CN"
    voice = LANGUAGE_TTS_VOICES.get(language, LANGUAGE_TTS_VOICES["zh-CN"])
    ready, message = check_tts_ready(language)
    return jsonify(
        {
            "provider": "edge-tts",
            "ready": ready,
            "voice": voice,
            "message": message,
            "languages": list(LANGUAGE_TTS_VOICES.keys()),
        }
    )


@app.get("/")
def index() -> Response:
    return send_from_directory(PUBLIC_DIR, "index.html")


@app.get("/resources/<path:filename>")
def resources(filename: str) -> Response:
    return send_from_directory(RESOURCES_DIR, filename)


@app.get("/<path:filename>")
def public_files(filename: str) -> Response:
    return send_from_directory(PUBLIC_DIR, filename)


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=False)
