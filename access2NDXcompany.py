import os
import pandas as pd
import time
import requests
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

def get_ndx_tickers():
    """直接使用纳斯达克官方API获取纳斯达克100指数成分股"""
    try:
        # 使用纳斯达克官方API
        url = "https://api.nasdaq.com/api/quote/list-type/nasdaq100"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # 解析JSON数据
        if 'data' in data and 'data' in data['data'] and 'rows' in data['data']['data']:
            tickers = [row['symbol'] for row in data['data']['data']['rows']]
            return tickers
        else:
            print("无法从API获取数据，返回结构不符合预期")
            return []
    except Exception as e:
        print(f"直接API方法出错: {e}")
        return []

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

# 主执行流程
if __name__ == "__main__":
    # 获取纳斯达克100指数成分股
    ndx_tickers = get_ndx_tickers()
    
    if not ndx_tickers:
        print("无法获取纳斯达克100指数成分股，程序终止。")
        exit(1)
    
    # 显示获取到的成分股信息
    print(f"\n成功获取到 {len(ndx_tickers)} 只纳斯达克100成分股")
    print("前10只股票:", ndx_tickers[:10])
    
    # 保存成分股列表到CSV
    tickers_df = pd.DataFrame({"Symbol": ndx_tickers})
    tickers_df.to_csv("nasdaq100_tickers.csv", index=False)
    print("成分股列表已保存到 nasdaq100_tickers.csv")
    
    # 获取所有成分股的详细信息
    companies_info = []
    for i, ticker in enumerate(ndx_tickers):
        print(f"正在获取第 {i+1}/{len(ndx_tickers)} 个公司信息: {ticker}")
        company_info = get_company_details(ticker)
        if company_info:
            companies_info.append(company_info)
        # 添加短暂延迟以避免API限制
        if i % 10 == 9:  # 每10个请求后暂停
            print("暂停2秒以避免API限制...")
            time.sleep(2)
    
    # 将公司信息保存到CSV文件
    if companies_info:
        df = pd.DataFrame(companies_info)
        current_date = datetime.now().strftime('%Y-%m-%d')
        output_file = f"nasdaq100_companies_{current_date}.csv"
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n公司信息已保存到 {output_file}")
        print(f"共获取到 {len(companies_info)} 家公司的信息")
    
    # 获取历史数据（可选）
    get_history = input("\n是否获取所有成分股的历史数据？(y/n): ").strip().lower()
    if get_history == 'y':
        days = int(input("请输入要获取的历史天数 (默认30天): ") or "30")
        
        all_history = []
        for i, ticker in enumerate(ndx_tickers):
            print(f"正在获取第 {i+1}/{len(ndx_tickers)} 个股票的历史数据: {ticker}")
            history = get_stock_history(ticker, days)
            if not history.empty:
                all_history.append(history)
            # 添加短暂延迟以避免API限制
            if i % 5 == 4:  # 每5个请求后暂停
                print("暂停1秒以避免API限制...")
                time.sleep(1)
        
        # 合并所有历史数据
        if all_history:
            history_df = pd.concat(all_history, ignore_index=True)
            history_file = f"nasdaq100_history_{days}days_{current_date}.csv"
            history_df.to_csv(history_file, index=False, encoding='utf-8')
            print(f"\n历史数据已保存到 {history_file}")
    
    print("\n处理完成!")