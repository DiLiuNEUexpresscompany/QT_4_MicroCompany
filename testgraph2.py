import networkx as nx
from community import community_louvain
from pyvis.network import Network

# -------------------------------
# 1. 加载并预处理图数据
# -------------------------------
# 从 GraphML 文件加载图
G = nx.read_graphml("nasdaq_lowprice_network.graphml")
print(f"原始图: 节点数量: {G.number_of_nodes()}, 边数量: {G.number_of_edges()}")

# 过滤出权重大于 0.95 的边
high_similarity_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('weight', 0) > 0.93]
# 使用 edge_subgraph() 提取子图，注意需要 .copy() 防止后续修改影响原图
G_filtered = G.edge_subgraph(high_similarity_edges).copy()

# 删除孤立节点（度为 0 的节点）
G_filtered = G_filtered.subgraph([n for n in G_filtered.nodes() if G_filtered.degree(n) > 0]).copy()
print(f"过滤后的图: 节点数量: {G_filtered.number_of_nodes()}, 边数量: {G_filtered.number_of_edges()}")

# -------------------------------
# 2. 计算节点属性（PageRank 和社区）
# -------------------------------
# 计算 PageRank 值
pr = nx.pagerank(G_filtered)

# 使用 Louvain 方法进行社区检测
try:
    communities = community_louvain.best_partition(G_filtered)
except Exception as e:
    print("社区检测失败，使用默认社区。")
    communities = {node: 0 for node in G_filtered.nodes()}

# 将 PageRank 和社区信息作为节点属性加入图中
for node in G_filtered.nodes():
    # 根据 PageRank 值设置节点大小（乘数可根据实际情况调整）
    G_filtered.nodes[node]['size'] = pr.get(node, 0) * 1000  
    # 将社区信息赋值给 group 属性，Pyvis 可根据该属性着色
    G_filtered.nodes[node]['group'] = communities.get(node, 0)

# -------------------------------
# 3. 生成交互式网络网页（Pyvis）
# -------------------------------
# 创建一个 Pyvis 网络对象
net = Network(height="800px", width="100%", bgcolor="#ffffff", font_color="black", directed=False)

# 将 NetworkX 图加载到 Pyvis 中（节点属性会自动传递）
net.from_nx(G_filtered)

# 添加物理引擎的控制面板（可选）
net.show_buttons(filter_=['physics'])

# 保存为交互式网页文件，注意将 notebook 参数设置为 False
html_file = "nasdaq_interactive_network.html"
net.show(html_file, notebook=False)
print(f"交互式网络图已保存为 {html_file}")

# -------------------------------
# 4. 输出网络统计信息及高相似度股票对
# -------------------------------
print("\n网络统计信息:")
print(f"平均聚类系数: {nx.average_clustering(G_filtered):.3f}")
if nx.is_connected(G_filtered):
    print(f"平均路径长度: {nx.average_shortest_path_length(G_filtered):.3f}")
else:
    print("图不连通，无法计算平均路径长度。")
print(f"网络密度: {nx.density(G_filtered):.3f}")

# 输出相似度最高的前 10 对股票（基于边的权重）
edge_weights = [(u, v, d['weight']) for u, v, d in G_filtered.edges(data=True)]
top_pairs = sorted(edge_weights, key=lambda x: x[2], reverse=True)[:10]
print("\n相似度最高的10对股票:")
for u, v, w in top_pairs:
    print(f"{u} - {v}: {w:.3f}")
