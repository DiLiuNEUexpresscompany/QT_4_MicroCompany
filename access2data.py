import os
import pandas as pd
from polygon import RESTClient
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 读取 API_KEY
API_KEY = os.getenv("POLYGON_STOCK_API")

# 检查 API_KEY 是否正确加载
if not API_KEY:
    raise ValueError("API Key 未找到，请在 .env 文件中设置 POLYGON_STOCK_API")

# 初始化 Polygon.io 客户端
client = RESTClient(api_key=API_KEY)

def get_low_price_stocks(date_str):
    """
    获取指定日期收盘价低于 5 美元的股票
    :param date_str: str, 格式 'YYYY-MM-DD'
    :return: List of (ticker, close_price)
    """
    low_price_stocks = []

    try:
        # 获取指定日期的股票数据
        response = client.get_grouped_daily_aggs(locale="us", market_type="stocks", date=date_str)

        # 遍历返回的数据
        for stock in response:
            try:
                ticker = stock.ticker  # ✅ 正确访问方式
                close_price = stock.close  # ✅ 正确访问方式

                if close_price is not None and close_price < 5:  # 筛选收盘价 < 5 美元的股票
                    low_price_stocks.append((ticker, close_price))

            except AttributeError as e:
                print(f"处理 {stock} 出错: {e}")

    except Exception as e:
        print(f"获取 {date_str} 的数据失败: {e}")

    return low_price_stocks

# 让用户输入查询日期
date_input = "2025-02-28"  # 示例日期

# 调用函数获取数据
low_price_stocks = get_low_price_stocks(date_input)

# 转换为 DataFrame 并展示
df = pd.DataFrame(low_price_stocks, columns=["Stock", "Yesterday Close"])

print("收盘价低于 5 美元的股票:")
print(df)
