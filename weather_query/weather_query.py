import requests
from typing import Any, Dict, Optional

CITY_CODES: Dict[str, str] = {
    # ...（此处省略，迁移自 app.py 的 CITY_CODES 字典）...
}

def get_city_code(city_name: str) -> Optional[str]:
    city_name = city_name.strip()
    if city_name in CITY_CODES:
        return CITY_CODES[city_name]
    for city, code in CITY_CODES.items():
        if city_name in city or city in city_name:
            return code
    return None

def get_weather(city: str) -> Dict[str, Any]:
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
        return {
            "success": False,
            "response": f"抱歉，网络异常，无法获取{city}的天气信息。",
        }
    except Exception:
        return {
            "success": False,
            "response": f"抱歉，查询{city}天气时发生错误。",
        }
