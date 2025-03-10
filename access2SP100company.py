import os
import pandas as pd
import requests
import time
from datetime import datetime
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

def get_sp500_from_wiki_api():
    """使用wikitable2json API获取标普500成分股"""
    try:
        # S&P 500的维基百科表格API
        url = "https://www.wikitable2json.com/api/List_of_S%26P_500_companies?table=0"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"API请求失败，状态码: {response.status_code}")
            return []
            
        data = response.json()
        
        # 检查API返回的数据结构 - 基于您分享的示例
        if not data or not isinstance(data, list) or len(data) == 0 or not isinstance(data[0], list):
            print("API返回的数据结构不符合预期")
            return []
            
        # 解析二维数组格式
        # 第一行是表头
        headers = data[0][0]
        # 查找Symbol列的索引
        symbol_index = headers.index("Symbol") if "Symbol" in headers else 0
        
        # 从第二行开始是数据
        tickers = []
        for i in range(1, len(data[0])):
            row = data[0][i]
            if len(row) > symbol_index:
                ticker = row[symbol_index].strip()
                if ticker:
                    tickers.append(ticker)
        
        return tickers
    except Exception as e:
        print(f"从wikitable2json API获取标普500数据时出错: {e}")
        return []

def get_company_details(ticker):
    """获取公司详细信息"""
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
            # 指数退避
            wait_time = (2 ** attempt) + (0.1 * attempt)
            print(f"等待 {wait_time:.2f} 秒后重试...")
            time.sleep(wait_time)

# 主执行流程
if __name__ == "__main__":
    print("正在获取标普500成分股数据...")
    
    # 获取标普500成分股
    sp500_tickers = get_sp500_from_wiki_api()
    
    if not sp500_tickers:
        print("无法获取标普500成分股，程序终止。")
        exit(1)
    
    # 显示获取到的成分股信息
    print(f"\n成功获取到 {len(sp500_tickers)} 只标普500成分股")
    print("前10只股票:", sp500_tickers[:10])
    
    # 保存所有标普500成分股到CSV
    tickers_df = pd.DataFrame({"Symbol": sp500_tickers})
    tickers_df.to_csv("sp500_tickers.csv", index=False)
    print("成分股列表已保存到 sp500_tickers.csv")
    
    # 获取每只股票的市值
    print("\n开始获取公司市值信息以识别标普100成分股...")
    companies_with_market_cap = []
    
    for i, ticker in enumerate(sp500_tickers):
        print(f"正在获取第 {i+1}/{len(sp500_tickers)} 个公司信息: {ticker}")
        company_info = get_company_details(ticker)
        
        if company_info and company_info['market_cap']:
            companies_with_market_cap.append({
                'ticker': ticker,
                'market_cap': company_info['market_cap']
            })
            print(f"获取到 {ticker} 的市值: {company_info['market_cap']}")
        
        # 添加短暂延迟以避免API限制
        if i % 5 == 4:  # 每5个请求后暂停
            print("暂停1秒以避免API限制...")
            time.sleep(1)
    
    # 按市值降序排序
    companies_with_market_cap.sort(key=lambda x: x['market_cap'], reverse=True)
    
    # 取前100家公司作为标普100的近似
    sp100_tickers = [company['ticker'] for company in companies_with_market_cap[:100]]
    
    # 显示获取到的标普100成分股信息
    print(f"\n通过市值排序获取到 {len(sp100_tickers)} 只标普100成分股")
    print("前10只股票:", sp100_tickers[:10])
    
    # 保存标普100成分股列表到CSV
    sp100_df = pd.DataFrame({"Symbol": sp100_tickers})
    sp100_df.to_csv("sp100_tickers.csv", index=False)
    print("标普100成分股列表已保存到 sp100_tickers.csv")
    
    # 获取标普100成分股的详细信息
    print("\n开始获取标普100成分股的详细信息...")
    companies_info = []
    
    for i, ticker in enumerate(sp100_tickers):
        print(f"正在获取第 {i+1}/{len(sp100_tickers)} 个公司详细信息: {ticker}")
        company_info = get_company_details(ticker)
        
        if company_info:
            companies_info.append(company_info)
        
        # 添加短暂延迟以避免API限制
        if i % 5 == 4:  # 每5个请求后暂停
            print("暂停1秒以避免API限制...")
            time.sleep(1)
    
    # 将公司信息保存到CSV文件
    if companies_info:
        df = pd.DataFrame(companies_info)
        current_date = datetime.now().strftime('%Y-%m-%d')
        output_file = f"sp100_companies_{current_date}.csv"
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n公司信息已保存到 {output_file}")
        print(f"共获取到 {len(companies_info)} 家公司的信息")
    
    print("\n处理完成!")