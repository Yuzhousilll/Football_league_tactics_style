#!/usr/bin/env python3
"""
分析球队风格因子随时间的演变
Analysis of team style factor evolution over time
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

# 因子中文名称
FACTOR_NAMES_CN = {
    'Factor1': '因子1: 进攻质量',
    'Factor2': '因子2: 防守积极性',
    'Factor3': '因子3: 侵略性',
    'Factor4': '因子4: 成熟度'
}

# 传统六强
TOP_6_TEAMS = [
    'Manchester City',
    'Liverpool', 
    'Chelsea',
    'Arsenal',
    'Manchester Utd',
    'Tottenham Hotspur'
]

def load_factor_scores(filepath):
    """加载因子得分数据"""
    df = pd.read_csv(filepath)
    # 提取赛季起始年份用于排序
    df['season_year'] = df['Season'].str.split('_').str[0].astype(int)
    df = df.sort_values(['Squad', 'season_year'])
    return df

def plot_top6_factor_evolution(df, output_dir):
    """绘制传统六强在各因子上的演变趋势"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('传统六强风格因子演变趋势 (2016-2025)', fontsize=16, fontweight='bold')
    
    factors = ['Factor1', 'Factor2', 'Factor3', 'Factor4']
    colors = plt.cm.Set2(range(len(TOP_6_TEAMS)))
    
    for idx, factor in enumerate(factors):
        ax = axes[idx // 2, idx % 2]
        
        for team_idx, team in enumerate(TOP_6_TEAMS):
            team_data = df[df['Squad'] == team].sort_values('season_year')
            if len(team_data) > 0:
                ax.plot(team_data['season_year'], team_data[factor], 
                       marker='o', label=team, linewidth=2, 
                       color=colors[team_idx], alpha=0.8)
        
        ax.set_title(FACTOR_NAMES_CN[factor], fontsize=12, fontweight='bold')
        ax.set_xlabel('赛季', fontsize=10)
        ax.set_ylabel('因子得分', fontsize=10)
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'top6_factor_evolution.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 已保存: {output_path}")
    plt.close()

def plot_league_factor_trends(df, output_dir):
    """绘制整个联赛在各因子上的平均趋势"""
    # 计算每个赛季的因子均值和标准差
    season_stats = df.groupby('season_year').agg({
        'Factor1': ['mean', 'std'],
        'Factor2': ['mean', 'std'],
        'Factor3': ['mean', 'std'],
        'Factor4': ['mean', 'std']
    }).reset_index()
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('英超联赛整体风格因子演变趋势 (2016-2025)', fontsize=16, fontweight='bold')
    
    factors = ['Factor1', 'Factor2', 'Factor3', 'Factor4']
    
    for idx, factor in enumerate(factors):
        ax = axes[idx // 2, idx % 2]
        
        years = season_stats['season_year']
        means = season_stats[(factor, 'mean')]
        stds = season_stats[(factor, 'std')]
        
        # 绘制均值线
        ax.plot(years, means, marker='o', linewidth=2.5, 
               color='#2E86AB', label='联赛平均值', markersize=8)
        
        # 添加标准差阴影区域
        ax.fill_between(years, means - stds, means + stds, 
                        alpha=0.2, color='#2E86AB', label='±1标准差')
        
        ax.set_title(FACTOR_NAMES_CN[factor], fontsize=12, fontweight='bold')
        ax.set_xlabel('赛季', fontsize=10)
        ax.set_ylabel('因子得分', fontsize=10)
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        
        # 添加趋势线
        z = np.polyfit(years, means, 1)
        p = np.poly1d(z)
        ax.plot(years, p(years), "r--", alpha=0.5, linewidth=1.5, label='趋势线')
        ax.legend(loc='best', fontsize=9)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'league_factor_trends.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 已保存: {output_path}")
    plt.close()

def find_biggest_changes(df, output_dir):
    """找出各因子上变化最大的球队"""
    results = []
    factors = ['Factor1', 'Factor2', 'Factor3', 'Factor4']
    
    for squad in df['Squad'].unique():
        squad_data = df[df['Squad'] == squad].sort_values('season_year')
        
        # 至少有3个赛季的数据才计算
        if len(squad_data) >= 3:
            for factor in factors:
                values = squad_data[factor].values
                # 计算变化幅度（最大值 - 最小值）
                change_range = values.max() - values.min()
                # 计算标准差（波动性）
                volatility = values.std()
                # 计算趋势（线性回归斜率）
                years = squad_data['season_year'].values
                if len(years) > 1:
                    slope = np.polyfit(years, values, 1)[0]
                else:
                    slope = 0
                
                results.append({
                    'Squad': squad,
                    'Factor': factor,
                    'Change_Range': change_range,
                    'Volatility': volatility,
                    'Trend_Slope': slope,
                    'Num_Seasons': len(squad_data)
                })
    
    results_df = pd.DataFrame(results)
    
    # 保存详细结果
    output_path = Path(output_dir) / 'factor_change_analysis.csv'
    results_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✓ 已保存: {output_path}")
    
    # 为每个因子找出变化最大的球队
    summary = []
    for factor in factors:
        factor_data = results_df[results_df['Factor'] == factor]
        
        # 按变化幅度排序
        top_by_range = factor_data.nlargest(5, 'Change_Range')[['Squad', 'Change_Range', 'Num_Seasons']]
        # 按波动性排序
        top_by_volatility = factor_data.nlargest(5, 'Volatility')[['Squad', 'Volatility', 'Num_Seasons']]
        # 上升趋势最大
        top_increasing = factor_data.nlargest(5, 'Trend_Slope')[['Squad', 'Trend_Slope', 'Num_Seasons']]
        # 下降趋势最大
        top_decreasing = factor_data.nsmallest(5, 'Trend_Slope')[['Squad', 'Trend_Slope', 'Num_Seasons']]
        
        summary.append({
            'factor': factor,
            'factor_name': FACTOR_NAMES_CN[factor],
            'top_by_range': top_by_range,
            'top_by_volatility': top_by_volatility,
            'top_increasing': top_increasing,
            'top_decreasing': top_decreasing
        })
    
    # 生成文本报告
    report_path = Path(output_dir) / 'factor_change_summary.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("球队风格因子变化分析总结\n")
        f.write("Team Style Factor Change Analysis Summary\n")
        f.write("=" * 80 + "\n\n")
        
        for item in summary:
            f.write(f"\n{'=' * 80}\n")
            f.write(f"{item['factor_name']}\n")
            f.write(f"{'=' * 80}\n\n")
            
            f.write("【变化幅度最大的5支球队】\n")
            f.write(item['top_by_range'].to_string(index=False))
            f.write("\n\n")
            
            f.write("【波动性最大的5支球队】\n")
            f.write(item['top_by_volatility'].to_string(index=False))
            f.write("\n\n")
            
            f.write("【上升趋势最显著的5支球队】\n")
            f.write(item['top_increasing'].to_string(index=False))
            f.write("\n\n")
            
            f.write("【下降趋势最显著的5支球队】\n")
            f.write(item['top_decreasing'].to_string(index=False))
            f.write("\n\n")
    
    print(f"✓ 已保存: {report_path}")
    return summary

def plot_individual_team_evolution(df, teams, output_dir):
    """为特定球队绘制详细的因子演变图"""
    for team in teams:
        team_data = df[df['Squad'] == team].sort_values('season_year')
        
        if len(team_data) < 2:
            print(f"⚠ {team} 数据不足，跳过")
            continue
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        factors = ['Factor1', 'Factor2', 'Factor3', 'Factor4']
        colors = ['#E63946', '#457B9D', '#2A9D8F', '#F4A261']
        
        for factor, color in zip(factors, colors):
            ax.plot(team_data['season_year'], team_data[factor], 
                   marker='o', label=FACTOR_NAMES_CN[factor], 
                   linewidth=2.5, color=color, markersize=8, alpha=0.8)
        
        ax.set_title(f'{team} 风格因子演变 (2016-2025)', fontsize=14, fontweight='bold')
        ax.set_xlabel('赛季', fontsize=11)
        ax.set_ylabel('因子得分', fontsize=11)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        safe_name = team.replace(' ', '_').replace('/', '_')
        output_path = Path(output_dir) / f'evolution_{safe_name}.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ 已保存: {output_path}")
        plt.close()

def create_heatmap_evolution(df, output_dir):
    """创建因子演变热力图"""
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle('英超球队风格因子演变热力图 (2016-2025)', fontsize=16, fontweight='bold')
    
    factors = ['Factor1', 'Factor2', 'Factor3', 'Factor4']
    
    for idx, factor in enumerate(factors):
        ax = axes[idx // 2, idx % 2]
        
        # 创建数据透视表：球队 x 赛季
        pivot_data = df.pivot(index='Squad', columns='season_year', values=factor)
        
        # 按最近赛季的得分排序
        if 2024 in pivot_data.columns:
            pivot_data = pivot_data.sort_values(2024, ascending=False)
        
        # 绘制热力图
        sns.heatmap(pivot_data, cmap='RdYlGn', center=0, 
                   annot=False, fmt='.2f', cbar_kws={'label': '因子得分'},
                   ax=ax, linewidths=0.5)
        
        ax.set_title(FACTOR_NAMES_CN[factor], fontsize=12, fontweight='bold')
        ax.set_xlabel('赛季', fontsize=10)
        ax.set_ylabel('球队', fontsize=10)
        
        # 调整刻度标签大小
        ax.tick_params(axis='both', labelsize=7)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'factor_evolution_heatmap.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 已保存: {output_path}")
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='分析球队风格因子演变')
    parser.add_argument('--input', default='data/derived/team_factor_scores_2016_2025.csv',
                       help='输入的因子得分CSV文件')
    parser.add_argument('--output-dir', default='data/derived',
                       help='输出目录')
    parser.add_argument('--individual-teams', nargs='+', 
                       help='需要单独分析的球队名称（可选）')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("球队风格因子演变分析")
    print("=" * 80)
    
    # 加载数据
    print(f"\n📂 加载数据: {args.input}")
    df = load_factor_scores(args.input)
    print(f"✓ 已加载 {len(df)} 条记录，{df['Squad'].nunique()} 支球队")
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 传统六强因子演变
    print("\n📊 绘制传统六强因子演变趋势...")
    plot_top6_factor_evolution(df, output_dir)
    
    # 2. 联赛整体趋势
    print("\n📊 绘制联赛整体因子趋势...")
    plot_league_factor_trends(df, output_dir)
    
    # 3. 因子演变热力图
    print("\n📊 绘制因子演变热力图...")
    create_heatmap_evolution(df, output_dir)
    
    # 4. 分析变化最大的球队
    print("\n🔍 分析因子变化最大的球队...")
    summary = find_biggest_changes(df, output_dir)
    
    # 5. 为传统六强生成单独的演变图
    print("\n📊 生成传统六强的详细演变图...")
    plot_individual_team_evolution(df, TOP_6_TEAMS, output_dir)
    
    # 6. 可选：为指定球队生成详细演变图
    if args.individual_teams:
        print(f"\n📊 生成指定球队的详细演变图...")
        plot_individual_team_evolution(df, args.individual_teams, output_dir)
    
    print("\n" + "=" * 80)
    print("✅ 分析完成！所有输出已保存到:", output_dir)
    print("=" * 80)

if __name__ == '__main__':
    main()
