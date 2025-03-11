import pandas as pd

def merge_index_companies():
    """合并 S&P100 和 NASDAQ100 的公司信息"""
    
    # 读取两个CSV文件
    sp100_path = "S&P100_company_info/sp100_companies_2025-03-10.csv"
    ndx_path = "NDX_company_info/nasdaq100_companies_2025-03-10.csv"
    
    try:
        sp100_df = pd.read_csv(sp100_path)
        ndx_df = pd.read_csv(ndx_path)
        
        # 合并数据框并去除重复项（基于ticker）
        merged_df = pd.concat([sp100_df, ndx_df])
        unique_df = merged_df.drop_duplicates(subset=['ticker'])
        
        # 按市值降序排序
        if 'market_cap' in unique_df.columns:
            unique_df = unique_df.sort_values(by='market_cap', ascending=False)
        
        # 保存结果
        output_file = "merged_indices_2025-03-10.csv"
        unique_df.to_csv(output_file, index=False)
        
        # 打印统计信息
        print(f"S&P 100 公司数量: {len(sp100_df)}")
        print(f"纳斯达克 100 公司数量: {len(ndx_df)}")
        print(f"合并后的唯一公司数量: {len(unique_df)}")
        print(f"数据已保存到: {output_file}")
        
    except FileNotFoundError as e:
        print(f"错误：找不到文件 - {e}")
    except Exception as e:
        print(f"处理过程中出现错误: {e}")

if __name__ == "__main__":
    merge_index_companies()