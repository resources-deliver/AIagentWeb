from datetime import datetime

def get_current_time(query_type: str) -> dict:
    """获取当前时间信息"""
    now = datetime.now()
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
        return {
            "weekday": weekday,
            "response": f"今天是{weekday}。",
        }
    else:  # full
        return {
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "weekday": weekday,
            "response": f"现在是 {now.strftime('%Y 年 %m 月 %d 日')} {weekday} {now.strftime('%H 点 %M 分')}",
        }
