import os
import pandas as pd
import time
from datetime import datetime, timedelta
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

def exponential_backoff(attempt):
    """实现指数退避策略"""
    wait_time = (2 ** attempt) + (0.1 * attempt)
    print(f"等待 {wait_time:.2f} 秒后重试...")
    time.sleep(wait_time)

def get_low_price_stocks(date_str):
    """
    获取指定日期收盘价低于 5 美元的股票
    :param date_str: str, 格式 'YYYY-MM-DD'
    :return: DataFrame with all stock data and a list of low price tickers
    """
    all_stocks_data = []
    low_price_tickers = []

    try:
        # 获取指定日期的股票数据
        response = client.get_grouped_daily_aggs(locale="us", market_type="stocks", date=date_str)

        # 遍历返回的数据
        for stock in response:
            try:
                stock_data = {
                    'ticker': stock.ticker,
                    'open': stock.open,
                    'high': stock.high,
                    'low': stock.low, 
                    'close': stock.close,
                    'volume': stock.volume,
                    'vwap': stock.vwap,
                    'date': date_str
                }
                
                all_stocks_data.append(stock_data)
                
                # 筛选收盘价 < 5 美元的股票
                if stock.close is not None and stock.close < 10:
                    low_price_tickers.append(stock.ticker)

            except AttributeError as e:
                print(f"处理 {stock} 出错: {e}")

    except Exception as e:
        print(f"获取 {date_str} 的数据失败: {e}")

    # 创建包含所有股票数据的 DataFrame
    all_stocks_df = pd.DataFrame(all_stocks_data)
    
    return all_stocks_df, low_price_tickers

def get_stock_history(ticker, days=30):
    """
    获取指定股票过去一个月的历史数据
    :param ticker: str, 股票代码
    :param days: int, 获取的天数
    :return: DataFrame with historical data
    """
    MAX_RETRIES = 3
    
    for attempt in range(MAX_RETRIES):
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            aggs = list(client.list_aggs(ticker, 1, 'day', start_date, end_date))
            
            history_data = [{
                'ticker': ticker,
                'date': datetime.fromtimestamp(agg.timestamp/1000).strftime('%Y-%m-%d'),
                'open': agg.open,
                'high': agg.high,
                'low': agg.low,
                'close': agg.close,
                'volume': agg.volume,
                'vwap': agg.vwap if hasattr(agg, 'vwap') else None,
                'transactions': agg.transactions if hasattr(agg, 'transactions') else None
            } for agg in aggs]
            
            return pd.DataFrame(history_data)
            
        except Exception as e:
            print(f"尝试 {attempt + 1} - 获取 {ticker} 历史数据失败: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                print(f"无法获取 {ticker} 的历史数据")
                return pd.DataFrame()  # 返回空 DataFrame
            exponential_backoff(attempt)

# 主执行流程
if __name__ == "__main__":
    # 让用户输入查询日期
    date_input = "2025-02-28"  # 示例日期，可以修改为用户输入
    
    # 获取当天所有股票数据和低价股票列表
    all_stocks_df, low_price_tickers = get_low_price_stocks(date_input)
    
    # 保存当天所有股票数据到 CSV
    low_price_stocks_csv = f"low_price_stocks_{date_input}.csv"
    low_price_df = all_stocks_df[all_stocks_df['ticker'].isin(low_price_tickers)]
    low_price_df.to_csv(low_price_stocks_csv, index=False)
    print(f"所有股票数据已保存到 {low_price_stocks_csv}")
    
    # 显示低价股票信息
    low_price_df = all_stocks_df[all_stocks_df['ticker'].isin(low_price_tickers)]
    print(f"\n收盘价低于 5 美元的股票数量: {len(low_price_tickers)}")
    print(low_price_df[['ticker', 'close']].head(10))  # 只显示前10个结果
    
    # 为每个低价股票获取过去一个月的历史数据
    print("\n正在获取低价股票的历史数据...")
    
    # 创建一个目录来存储历史数据
    history_dir = "stock_history"
    os.makedirs(history_dir, exist_ok=True)
    
    # 合并所有历史数据的DataFrame
    all_history_data = pd.DataFrame()
    
    # 只处理前50个低价股票，以防API限制
    process_limit = min(50, len(low_price_tickers))
    
    for i, ticker in enumerate(low_price_tickers[:process_limit]):
        print(f"处理 {i+1}/{process_limit}: {ticker}")
        history_df = get_stock_history(ticker)
        
        if not history_df.empty:
            # 添加到合并的DataFrame
            all_history_data = pd.concat([all_history_data, history_df])
            
            # 也可以单独保存每个股票的历史数据
            history_file = os.path.join(history_dir, f"{ticker}_history.csv")
            history_df.to_csv(history_file, index=False)
    
    # 保存所有低价股票的历史数据到一个CSV文件
    if not all_history_data.empty:
        combined_history_file = f"low_price_stocks_history_{date_input}.csv"
        all_history_data.to_csv(combined_history_file, index=False)
        print(f"\n所有低价股票的历史数据已保存到 {combined_history_file}")
    
    print("\n处理完成!")