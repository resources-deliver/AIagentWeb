import requests

def get_stock_price_cn(ticker: str) -> dict:
    """
    查询中国A股实时股价（新浪财经接口）
    :param ticker: 6位股票代码，如600519
    :return: dict，包含股票名称、当前价、开盘价、昨收、最高、最低等
    """
    try:
        if ticker.startswith("6"):
            code = f"sh{ticker}"
        else:
            code = f"sz{ticker}"
        url = f"https://hq.sinajs.cn/list={code}"
        headers = {"Referer": "https://finance.sina.com/"}
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()
        data = res.text.split('"')[1].split(',')
        if len(data) < 3:
            return {"status": "error", "message": f"未找到股票：{ticker}"}
        return {
            "status": "ok",
            "name": data[0],
            "ticker": ticker,
            "current_price": float(data[3]),
            "open": float(data[1]),
            "last_close": float(data[2]),
            "high": float(data[4]),
            "low": float(data[5]),
            "time": data[30] + ' ' + data[31] if len(data) > 31 else ""
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
