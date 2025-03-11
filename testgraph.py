import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from community import community_louvain

# 加载图
G = nx.read_graphml("nasdaq_lowprice_network.graphml")
print(f"原始图: 节点数量: {G.number_of_nodes()}, 边数量: {G.number_of_edges()}")

# 创建一个只包含权重大于0.95的边的子图
high_similarity_edges = [(u, v) for (u, v, d) in G.edges(data=True) if d.get('weight', 0) > 0.95]
G_filtered = G.edge_subgraph(high_similarity_edges)

# 只保留有连接的节点（删除孤立节点）
G_filtered = G_filtered.subgraph([n for n in G_filtered.nodes() if G_filtered.degree(n) > 0])
print(f"过滤后的图: 节点数量: {G_filtered.number_of_nodes()}, 边数量: {G_filtered.number_of_edges()}")

def visualize_high_similarity_network(G, output_file="high_similarity_nasdaq_network.png"):
    """可视化高相似度网络"""
    plt.figure(figsize=(20, 20), dpi=300)
    
    # 使用 spring_layout 布局，增加节点间距
    pos = nx.spring_layout(G, k=1, iterations=100, seed=42)
    
    # 计算节点的PageRank值用于节点大小
    pr = nx.pagerank(G)
    
    # 尝试进行社区检测
    try:
        communities = community_louvain.best_partition(G)
        node_colors = [communities[node] for node in G.nodes()]
        cmap = plt.cm.get_cmap('tab20', max(communities.values()) + 1)
    except:
        node_colors = list(dict(G.degree()).values())
        cmap = plt.cm.viridis
    
    # 设置节点大小
    node_sizes = [8000 * pr[node] for node in G.nodes()]
    
    # 绘制节点
    nodes = nx.draw_networkx_nodes(G, pos,
                                 node_size=node_sizes,
                                 node_color=node_colors,
                                 cmap=cmap,
                                 alpha=0.7,
                                 edgecolors='white',
                                 linewidths=1)
    
    # 绘制边，使用权重来决定边的粗细
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    nx.draw_networkx_edges(G, pos,
                          alpha=0.5,
                          width=[3 * w for w in edge_weights],
                          edge_color='gray')
    
    # 绘制所有节点的标签
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
    
    # 添加标题和说明
    plt.title("NASDAQ高相似度股票网络\n(相似度 > 0.95)", 
             fontsize=20, 
             fontweight='bold', 
             pad=20)
    
    # 添加图例说明
    legend_text = (
        "节点颜色：不同社区群组\n"
        "节点大小：PageRank中心性\n"
        "边的粗细：相似度强度\n"
        f"节点数量：{G.number_of_nodes()}\n"
        f"边数量：{G.number_of_edges()}"
    )
    plt.text(0.02, 0.02, legend_text,
             transform=plt.gca().transAxes,
             fontsize=14,
             bbox=dict(facecolor='white', alpha=0.8))
    
    plt.axis('off')
    plt.tight_layout()
    
    # 保存高分辨率图像
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"图像已保存为 {output_file}")
    plt.show()

# 可视化高相似度网络
visualize_high_similarity_network(G_filtered)

# 导出到Gephi
nx.write_gexf(G_filtered, "nasdaq_high_similarity_network.gexf")
print("已导出高相似度网络到 nasdaq_high_similarity_network.gexf，可在Gephi中打开")

# 打印一些网络统计信息
print("\n网络统计信息:")
print(f"平均聚类系数: {nx.average_clustering(G_filtered):.3f}")
print(f"平均路径长度: {nx.average_shortest_path_length(G_filtered):.3f}")
print(f"网络密度: {nx.density(G_filtered):.3f}")

# 打印相似度最高的前10对股票
edge_weights = [(u, v, d['weight']) for u, v, d in G_filtered.edges(data=True)]
top_pairs = sorted(edge_weights, key=lambda x: x[2], reverse=True)[:10]
print("\n相似度最高的10对股票:")
for u, v, w in top_pairs:
    print(f"{u} - {v}: {w:.3f}")