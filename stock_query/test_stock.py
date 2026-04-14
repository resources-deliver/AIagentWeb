import requests
import json

def get_stock_price_cn(ticker):
    """
    新浪财经 A 股实时行情接口
    :param ticker: 6 位股票代码，如 600519
    """
    try:
        # 自动判断市场：6开头=沪市(sh)，0/3开头=深市(sz)
        if ticker.startswith("6"):
            code = f"sh{ticker}"
        else:
            code = f"sz{ticker}"

        # 新浪官方免费接口
        url = f"https://hq.sinajs.cn/list={code}"
        headers = {"Referer": "https://finance.sina.com/"}
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()

        # 解析返回数据
        data = res.text.split('"')[1].split(',')

        # 股票没找到/停牌
        if len(data) < 3:
            return json.dumps({
                "status": "error",
                "message": f"未找到股票：{ticker}"
            }, ensure_ascii=False)

        # 字段说明
        result = {
            "name": data[0],                # 股票名称
            "ticker": ticker,               # 股票代码
            "current_price": float(data[3]),# 当前价
            "open": float(data[1]),         # 开盘价
            "last_close": float(data[2]),   # 昨收价
            "high": float(data[4]),         # 最高
            "low": float(data[5]),          # 最低
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)
