#!/usr/bin/env python3
"""
因子分析模型评价与诊断
Evaluate and diagnose factor analysis model quality
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import FactorAnalysis
from scipy.stats import chi2
from itertools import combinations

def calculate_kmo(corr_matrix):
    """计算 Kaiser-Meyer-Olkin (KMO) 指标"""
    n_vars = corr_matrix.shape[0]
    
    # 计算逆相关矩阵
    inverse_corr = np.linalg.inv(corr_matrix)
    
    # 计算偏相关系数
    partial_corr = -inverse_corr / np.sqrt(np.outer(np.diag(inverse_corr), np.diag(inverse_corr)))
    
    # KMO公式：sum(r_ij^2) / [sum(r_ij^2) + sum(partial_r_ij^2)]
    r_squared = (corr_matrix ** 2).sum() - n_vars  # 去掉对角线的1
    partial_r_squared = (partial_corr ** 2).sum() - n_vars
    
    kmo = r_squared / (r_squared + partial_r_squared)
    
    # 计算每个变量的偏KMO
    var_kmo = np.zeros(n_vars)
    for i in range(n_vars):
        r_sq = ((corr_matrix[i, :] ** 2).sum() - 1)
        p_sq = ((partial_corr[i, :] ** 2).sum() - 1)
        var_kmo[i] = r_sq / (r_sq + p_sq) if (r_sq + p_sq) > 0 else 0
    
    return kmo, var_kmo

def bartlett_test(corr_matrix, n_samples):
    """计算 Bartlett 球形检验统计量"""
    n_vars = corr_matrix.shape[0]
    det_corr = np.linalg.det(corr_matrix)
    
    # Bartlett统计量
    chi_sq = -(n_samples - 1 - (2 * n_vars + 5) / 6) * np.log(det_corr)
    df = n_vars * (n_vars - 1) / 2
    p_value = 1 - chi2.cdf(chi_sq, df)
    
    return chi_sq, df, p_value

def evaluate_factor_model(data_path, output_path='factor_evaluation.txt'):
    """完整评价因子分析模型"""
    
    # 加载数据
    df = pd.read_csv(data_path)
    
    # 选择因子分析变量
    factor_vars = [
        "shots_on_target_per_match",
        "goals_per_sot",
        "cross_share_of_touches",
        "offsides_per_match",
        "tackles_won_per_match",
        "interceptions_per_match",
        "shots_on_target_against_per_match",
        "save_pct",
        "fouls_drawn_per_match",
    ]
    
    X = df[factor_vars].dropna()
    n_samples = X.shape[0]
    n_vars = X.shape[1]
    
    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 计算相关矩阵
    corr_matrix = np.corrcoef(X_scaled, rowvar=False)
    
    # 计算KMO
    kmo, var_kmo = calculate_kmo(corr_matrix)
    
    # Bartlett检验
    chi_sq, df, p_value = bartlett_test(corr_matrix, n_samples)
    
    # 拟合4因子模型
    fa = FactorAnalysis(n_components=4, random_state=42, max_iter=1000)
    fa.fit(X_scaled)
    
    # 获取因子载荷
    # 载荷 = components_.T * sqrt(特征值/误差方差)
    # 简化: 直接使用components_作为标准化载荷
    loadings = fa.components_.T  # 形状: (9, 4)
    
    # 计算共同度 (communalities)
    communalities = (loadings ** 2).sum(axis=1)
    
    # 计算特异性 (uniqueness)
    uniqueness = fa.noise_variance_
    
    # 计算解释方差
    # 因子方差 = 每个因子载荷平方和
    factor_variance = (loadings ** 2).sum(axis=0)
    total_variance = n_vars  # 标准化后总方差=变量数
    variance_explained = factor_variance / total_variance * 100
    cumsum_variance = np.cumsum(variance_explained)
    
    # 生成评估报告
    report = []
    report.append("=" * 80)
    report.append("因子分析模型评价报告")
    report.append("=" * 80)
    report.append("")
    
    # 1. 数据适用性检验
    report.append("1. 数据适用性检验 (Sampling Adequacy)")
    report.append("-" * 80)
    report.append(f"样本量: {n_samples} (建议≥100，最佳≥150)")
    report.append(f"变量数: {n_vars}")
    report.append(f"样本/变量比: {n_samples/n_vars:.2f}:1 (建议≥3:1)")
    report.append("")
    
    report.append("KMO (Kaiser-Meyer-Olkin) 检验:")
    report.append(f"  整体KMO值: {kmo:.4f}")
    kmo_interpretation = ""
    if kmo >= 0.9:
        kmo_interpretation = "优秀"
    elif kmo >= 0.8:
        kmo_interpretation = "很好"
    elif kmo >= 0.7:
        kmo_interpretation = "可以"
    elif kmo >= 0.6:
        kmo_interpretation = "一般"
    elif kmo >= 0.5:
        kmo_interpretation = "勉强"
    else:
        kmo_interpretation = "不适合"
    report.append(f"  解释: {kmo_interpretation} (>0.5为可接受)")
    report.append("")
    report.append("  各变量的KMO值:")
    for i, var in enumerate(factor_vars):
        report.append(f"    {var:40s}: {var_kmo[i]:.4f}")
    report.append("")
    
    report.append("Bartlett 球形检验:")
    report.append(f"  卡方统计量: {chi_sq:.4f}")
    report.append(f"  自由度: {int(df)}")
    report.append(f"  p-value: {p_value:.4e}")
    if p_value < 0.001:
        report.append(f"  结论: 强烈拒绝零假设 (p<0.001)，数据适合因子分析")
    elif p_value < 0.05:
        report.append(f"  结论: 拒绝零假设 (p<0.05)，数据适合因子分析")
    else:
        report.append(f"  结论: 未能拒绝零假设，数据可能不适合因子分析")
    report.append("")
    
    # 2. 因子模型拟合质量
    report.append("2. 因子模型拟合质量评价")
    report.append("-" * 80)
    report.append("共同度 (Communalities) - 每个变量被因子解释的方差比例:")
    report.append("")
    comm_df = pd.DataFrame({
        '变量': factor_vars,
        '共同度': communalities,
        '特异性': uniqueness,
        '解释度%': communalities * 100
    })
    report.append(comm_df.to_string(index=False))
    report.append("")
    report.append(f"共同度平均值: {communalities.mean():.4f}")
    report.append(f"共同度范围: {communalities.min():.4f} - {communalities.max():.4f}")
    if communalities.mean() > 0.6:
        report.append("✓ 评价: 良好 (平均>0.6)")
    elif communalities.mean() > 0.5:
        report.append("○ 评价: 可接受 (平均>0.5)")
    else:
        report.append("✗ 评价: 欠佳 (平均<0.5)")
    report.append("")
    
    # 3. 因子解释方差
    report.append("3. 因子解释方差")
    report.append("-" * 80)
    var_df = pd.DataFrame({
        '因子': [f'Factor {i+1}' for i in range(4)],
        '方差贡献': factor_variance,
        '贡献率%': variance_explained,
        '累计贡献率%': cumsum_variance
    })
    report.append(var_df.to_string(index=False))
    report.append("")
    report.append(f"4个因子累计解释方差: {cumsum_variance[-1]:.2f}%")
    if cumsum_variance[-1] > 70:
        report.append("✓ 评价: 良好 (>70%)")
    elif cumsum_variance[-1] > 60:
        report.append("○ 评价: 可接受 (60-70%)")
    else:
        report.append("✗ 评价: 欠佳 (<60%)")
    report.append("")
    
    # 4. 因子载荷质量评估
    report.append("4. 因子载荷质量评估")
    report.append("-" * 80)
    
    # 统计绝对值>0.5、>0.6、>0.7的载荷
    abs_loadings = np.abs(loadings)
    high_load_05 = (abs_loadings > 0.5).sum()
    high_load_06 = (abs_loadings > 0.6).sum()
    high_load_07 = (abs_loadings > 0.7).sum()
    
    report.append(f"高质量载荷（|载荷|>0.5）: {high_load_05}/{n_vars*4} = {high_load_05/(n_vars*4)*100:.1f}%")
    report.append(f"优质载荷（|载荷|>0.6）: {high_load_06}/{n_vars*4} = {high_load_06/(n_vars*4)*100:.1f}%")
    report.append(f"极优载荷（|载荷|>0.7）: {high_load_07}/{n_vars*4} = {high_load_07/(n_vars*4)*100:.1f}%")
    report.append("")
    if high_load_05 / (n_vars*4) > 0.5:
        report.append("✓ 评价: 良好 (>50%载荷>0.5)")
    else:
        report.append("○ 评价: 一般 (高质量载荷不足)")
    report.append("")
    
    # 5. 总体评价
    report.append("5. 总体模型评价")
    report.append("-" * 80)
    
    score = 0
    details = []
    
    # KMO评分
    if kmo >= 0.7:
        score += 2
        details.append(f"✓ KMO={kmo:.3f} (>0.7，优秀)")
    elif kmo >= 0.6:
        score += 1
        details.append(f"○ KMO={kmo:.3f} (0.6-0.7，可接受)")
    else:
        details.append(f"✗ KMO={kmo:.3f} (<0.6，欠佳)")
    
    # Bartlett评分
    if p_value < 0.001:
        score += 2
        details.append("✓ Bartlett检验: p<0.001 (显著，适合因子分析)")
    elif p_value < 0.05:
        score += 1
        details.append("○ Bartlett检验: p<0.05 (基本适合)")
    else:
        details.append("✗ Bartlett检验: p>0.05 (不显著，不适合)")
    
    # 共同度评分
    if communalities.mean() > 0.6:
        score += 2
        details.append(f"✓ 共同度: {communalities.mean():.3f} (>0.6，良好)")
    elif communalities.mean() > 0.5:
        score += 1
        details.append(f"○ 共同度: {communalities.mean():.3f} (0.5-0.6，可接受)")
    else:
        details.append(f"✗ 共同度: {communalities.mean():.3f} (<0.5，欠佳)")
    
    # 解释方差评分
    if cumsum_variance[-1] > 70:
        score += 2
        details.append(f"✓ 解释方差: {cumsum_variance[-1]:.1f}% (>70%，良好)")
    elif cumsum_variance[-1] > 60:
        score += 1
        details.append(f"○ 解释方差: {cumsum_variance[-1]:.1f}% (60-70%，可接受)")
    else:
        details.append(f"✗ 解释方差: {cumsum_variance[-1]:.1f}% (<60%，欠佳)")
    
    for detail in details:
        report.append(detail)
    
    report.append("")
    report.append("总体评分: {}/8".format(score))
    if score >= 7:
        report.append("★★★ 模型优秀，可用于后续分析")
    elif score >= 5:
        report.append("★★ 模型可接受，有一定局限性")
    elif score >= 3:
        report.append("★ 模型有缺陷，需要改进")
    else:
        report.append("✗ 模型不适合，需要重新考虑")
    
    report.append("")
    report.append("=" * 80)
    
    # 保存报告
    report_text = "\n".join(report)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\n报告已保存到: {output_path}")

if __name__ == '__main__':
    evaluate_factor_model('style_metrics_all.csv', 
                         'data/derived/factor_evaluation.txt')
