#!/usr/bin/env python3
"""
简化版因子演变分析（适用于2-4个因子的任何版本）
Simplified factor evolution analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import argparse

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

TOP_6_TEAMS = [
    'Manchester City',
    'Liverpool', 
    'Chelsea',
    'Arsenal',
    'Manchester Utd',
    'Tottenham Hotspur'
]

def load_data(filepath):
    """加载因子得分数据"""
    df = pd.read_csv(filepath)
    df['season_year'] = df['Season'].str.split('_').str[0].astype(int)
    df = df.sort_values(['Squad', 'season_year'])
    
    # 自动检测因子列
    factor_cols = [col for col in df.columns if col.startswith('Factor')]
    return df, factor_cols

def plot_top6_evolution(df, factor_cols, output_dir):
    """绘制传统六强因子演变"""
    n_factors = len(factor_cols)
    
    if n_factors == 2:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        axes = [axes[0], axes[1]]
    elif n_factors == 3:
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    else:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = [axes[0,0], axes[0,1], axes[1,0], axes[1,1]][:n_factors]
    
    fig.suptitle(f'传统六强因子演变 (2016-2025) - {n_factors}因子版', 
                 fontsize=14, fontweight='bold')
    
    colors = plt.cm.Set2(range(len(TOP_6_TEAMS)))
    
    for idx, factor in enumerate(factor_cols):
        ax = axes[idx]
        
        for team_idx, team in enumerate(TOP_6_TEAMS):
            team_data = df[df['Squad'] == team].sort_values('season_year')
            if len(team_data) > 0:
                ax.plot(team_data['season_year'], team_data[factor], 
                       marker='o', label=team, linewidth=2, color=colors[team_idx])
        
        ax.set_title(f'{factor}', fontsize=11, fontweight='bold')
        ax.set_xlabel('Season', fontsize=10)
        ax.set_ylabel('Score', fontsize=10)
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.2)
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'top6_factor_evolution_simplified.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 已保存: {output_path}")
    plt.close()

def plot_league_trends(df, factor_cols, output_dir):
    """绘制联赛整体因子趋势"""
    season_stats = df.groupby('season_year')[factor_cols].agg(['mean', 'std']).reset_index()
    
    n_factors = len(factor_cols)
    if n_factors == 2:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        axes = [axes[0], axes[1]]
    elif n_factors == 3:
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    else:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = [axes[0,0], axes[0,1], axes[1,0], axes[1,1]][:n_factors]
    
    fig.suptitle(f'英超联赛因子趋势 (2016-2025) - {n_factors}因子版', 
                 fontsize=14, fontweight='bold')
    
    for idx, factor in enumerate(factor_cols):
        ax = axes[idx]
        
        years = season_stats['season_year']
        means = season_stats[(factor, 'mean')]
        stds = season_stats[(factor, 'std')]
        
        ax.plot(years, means, marker='o', linewidth=2.5, color='#2E86AB', markersize=8)
        ax.fill_between(years, means - stds, means + stds, alpha=0.2, color='#2E86AB')
        
        # 趋势线
        z = np.polyfit(years, means, 1)
        p = np.poly1d(z)
        ax.plot(years, p(years), "r--", alpha=0.5, linewidth=1.5)
        
        ax.set_title(f'{factor} Trend', fontsize=11, fontweight='bold')
        ax.set_xlabel('Season', fontsize=10)
        ax.set_ylabel('Mean Score', fontsize=10)
        ax.grid(True, alpha=0.2)
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'league_factor_trends_simplified.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 已保存: {output_path}")
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Simplified factor evolution analysis')
    parser.add_argument('--input', default='data/derived/team_factor_scores_6vars_2016_2025.csv',
                       help='Input factor scores CSV')
    parser.add_argument('--output-dir', default='data/derived',
                       help='Output directory')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("简化版因子演变分析 (Simplified Factor Evolution Analysis)")
    print("=" * 80)
    
    # 加载数据
    print(f"\n📂 加载数据: {args.input}")
    df, factor_cols = load_data(args.input)
    print(f"✓ 已加载 {len(df)} 条记录，{df['Squad'].nunique()} 支球队")
    print(f"✓ 检测到 {len(factor_cols)} 个因子: {', '.join(factor_cols)}")
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 传统六强演变
    print(f"\n📊 绘制传统六强因子演变...")
    plot_top6_evolution(df, factor_cols, output_dir)
    
    # 2. 联赛整体趋势
    print(f"\n📊 绘制联赛整体因子趋势...")
    plot_league_trends(df, factor_cols, output_dir)
    
    print("\n" + "=" * 80)
    print("✅ 演变分析完成！")
    print("=" * 80)

if __name__ == '__main__':
    main()
