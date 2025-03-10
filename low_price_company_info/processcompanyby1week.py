import os
import glob
import pandas as pd

# 定义存放CSV文件的文件夹路径
folder_path = "company_info"

# 获取该文件夹下所有CSV文件的路径
csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
print(f"读取到的CSV文件: {csv_files}")

# 读取所有CSV文件并存入列表中
dfs = []
for file in csv_files:
    df = pd.read_csv(file)
    dfs.append(df)

# 合并所有DataFrame
all_data = pd.concat(dfs, ignore_index=True)

# 根据公司名称去重（假设公司名称在 'name' 列中）
union_data = all_data.drop_duplicates(subset=['ticker'])

# 保存最终的并集数据到CSV文件
final_output = "final_union_by_ticker.csv"
union_data.to_csv(final_output, index=False, encoding='utf-8')
print(f"最终基于公司名称去重的并集已保存到 {final_output}")
