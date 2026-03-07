#!/usr/bin/env python3
"""Extract typical team examples for each cluster."""

import numpy as np
import pandas as pd

clusters = pd.read_csv('data/derived/team_clusters_assigned.csv')

cluster_examples = []

for cluster_id in sorted(clusters['Cluster'].unique()):
    cluster_data = clusters[clusters['Cluster'] == cluster_id]
    
    factor_cols = ['Factor1', 'Factor2', 'Factor3', 'Factor4']
    
    cluster_center = cluster_data[factor_cols].mean()
    cluster_data_copy = cluster_data.copy()
    cluster_data_copy['distance'] = np.sqrt(((cluster_data[factor_cols] - cluster_center) ** 2).sum(axis=1))
    
    typical_teams = cluster_data_copy.nsmallest(5, 'distance')[['Season', 'Squad', 'Factor1', 'Factor2', 'Factor3', 'Factor4']]
    
    for _, row in typical_teams.iterrows():
        cluster_examples.append({
            'Cluster': cluster_id,
            'Season': row['Season'],
            'Squad': row['Squad'],
            'Factor1': round(row['Factor1'], 2),
            'Factor2': round(row['Factor2'], 2),
            'Factor3': round(row['Factor3'], 2),
            'Factor4': round(row['Factor4'], 2),
        })

examples_df = pd.DataFrame(cluster_examples)
examples_df.to_csv('data/derived/cluster_typical_examples.csv', index=False)

print("=== 各聚类典型球队 ===\n")

cluster_names = {
    0: "中游防守型",
    1: "高位压迫型",
    2: "顶级进攻型", 
    3: "保级/弱旅型"
}

for cluster_id in sorted(clusters['Cluster'].unique()):
    print(f"Cluster {cluster_id} ({cluster_names[cluster_id]}):")
    print(examples_df[examples_df['Cluster'] == cluster_id][['Season', 'Squad']].to_string(index=False))
    print()

print("\n=== 聚类分布摘要 ===")
for cluster_id in sorted(clusters['Cluster'].unique()):
    count = len(clusters[clusters['Cluster'] == cluster_id])
    print(f"Cluster {cluster_id} ({cluster_names[cluster_id]}): {count}支球队")

print("\n已生成: data/derived/cluster_typical_examples.csv")
