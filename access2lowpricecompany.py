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
    获取指定日期收盘价低于 10 美元的股票
    :param date_str: str, 格式 'YYYY-MM-DD'
    :return: DataFrame with all stock data and a list of low price tickers
    """
    low_price_tickers = []

    try:
        # 获取指定日期的股票数据
        response = client.get_grouped_daily_aggs(locale="us", market_type="stocks", date=date_str)

        # 遍历返回的数据
        for stock in response:
            try:                
                # 筛选收盘价 < 10 美元的股票
                if stock.close is not None and stock.close < 10:
                    low_price_tickers.append(stock.ticker)

            except AttributeError as e:
                print(f"处理 {stock} 出错: {e}")

    except Exception as e:
        print(f"获取 {date_str} 的数据失败: {e}")
    
    return low_price_tickers

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

def get_company_details(ticker):
    """
    获取公司详细信息
    :param ticker: str, 股票代码
    :return: dict, 公司详细信息
    """
    MAX_RETRIES = 3
    
    for attempt in range(MAX_RETRIES):
        try:
            # 获取公司详细信息
            details = client.get_ticker_details(ticker)
            
            # 提取所需信息
            company_info = {
                'ticker': ticker,
                'name': details.name if hasattr(details, 'name') else None,
                'description': details.description if hasattr(details, 'description') else None,
                'cik': details.cik if hasattr(details, 'cik') else None,
                'composite_figi': details.composite_figi if hasattr(details, 'composite_figi') else None,
                'market_cap': details.market_cap if hasattr(details, 'market_cap') else None,
                'weighted_shares_outstanding': details.weighted_shares_outstanding if hasattr(details, 'weighted_shares_outstanding') else None,
                'share_class_shares_outstanding': details.share_class_shares_outstanding if hasattr(details, 'share_class_shares_outstanding') else None,
                'sic_code': details.sic_code if hasattr(details, 'sic_code') else None,
                'sic_description': details.sic_description if hasattr(details, 'sic_description') else None,
                'homepage_url': details.homepage_url if hasattr(details, 'homepage_url') else None,
                'type': details.type if hasattr(details, 'type') else None
            }
            
            return company_info
            
        except Exception as e:
            print(f"尝试 {attempt + 1} - 获取 {ticker} 公司信息失败: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                return None
            exponential_backoff(attempt)

# 修改主执行流程
if __name__ == "__main__":
    # 让用户输入查询日期
    date_input = "2025-03-04"  # 示例日期，可以修改为用户输入
    
    # 获取当天所有股票数据和低价股票列表
    low_price_tickers = get_low_price_stocks(date_input)
    
    # 显示低价股票信息
    print(f"\n收盘价低于 10 美元的股票数量: {len(low_price_tickers)}")
    
    # 获取所有低价股票的详细信息
    companies_info = []
    for i, ticker in enumerate(low_price_tickers):
        print(f"正在获取第 {i+1}/{len(low_price_tickers)} 个公司信息: {ticker}")
        company_info = get_company_details(ticker)
        if company_info:
            companies_info.append(company_info)
    
    # 将公司信息保存到CSV文件
    if companies_info:
        df = pd.DataFrame(companies_info)
        output_file = f"low_price_companies_{date_input}.csv"
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n公司信息已保存到 {output_file}")
        print(f"共获取到 {len(companies_info)} 家公司的信息")
    
    print("\n处理完成!")