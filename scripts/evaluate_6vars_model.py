#!/usr/bin/env python3
"""
6变量版因子分析模型评价
"""

import pandas as pd
import numpy as np

def evaluate_fa_6vars():
    """评价6变量版因子分析结果"""
    
    # 加载因子载荷
    loadings_df = pd.read_csv('data/derived/team_factor_loadings_6vars_2016_2025.csv')
    
    variables = loadings_df['variable'].values
    factor_cols = [col for col in loadings_df.columns if col.startswith('Factor')]
    loadings = loadings_df[factor_cols].values
    communalities = loadings_df['communality'].values
    
    n_vars = len(variables)
    n_factors = len(factor_cols)
    n_samples = 180
    
    # 加载原始数据计算相关矩阵
    style_df = pd.read_csv('style_metrics_all.csv')
    
    factor_vars = [
        "shots_on_target_per_match",
        "goals_per_sot",
        "cross_share_of_touches",
        "tackles_won_per_match",
        "interceptions_per_match",
        "shots_on_target_against_per_match",
    ]
    
    X = style_df[factor_vars].dropna()
    from sklearn.preprocessing import StandardScaler
    X_scaled = StandardScaler().fit_transform(X)
    
    corr = np.corrcoef(X_scaled, rowvar=False)
    
    # ===== KMO计算 =====
    def calc_kmo(corr_matrix):
        n_vars = corr_matrix.shape[0]
        inv_corr = np.linalg.inv(corr_matrix)
        partial_corr = -inv_corr / np.sqrt(np.outer(np.diag(inv_corr), np.diag(inv_corr)))
        
        r2 = (corr_matrix ** 2).sum() - n_vars
        pr2 = (partial_corr ** 2).sum() - n_vars
        
        kmo = r2 / (r2 + pr2)
        
        var_kmo = np.zeros(n_vars)
        for i in range(n_vars):
            r2_i = (corr_matrix[i, :] ** 2).sum() - 1
            pr2_i = (partial_corr[i, :] ** 2).sum() - 1
            var_kmo[i] = r2_i / (r2_i + pr2_i) if (r2_i + pr2_i) > 0 else 0
        
        return kmo, var_kmo
    
    kmo_overall, kmo_vars = calc_kmo(corr)
    
    # ===== Bartlett检验 =====
    from scipy.stats import chi2
    det_corr = np.linalg.det(corr)
    chi_sq = -(n_samples - 1 - (2 * n_vars + 5) / 6) * np.log(det_corr)
    df = n_vars * (n_vars - 1) / 2
    p_value = 1 - chi2.cdf(chi_sq, df)
    
    # ===== 计算因子解释方差 =====
    factor_variance = (loadings ** 2).sum(axis=0)
    total_variance = n_vars
    var_explained = factor_variance / total_variance * 100
    cumsum_var = np.cumsum(var_explained)
    
    # ===== 生成报告 =====
    report = []
    report.append("=" * 90)
    report.append("因子分析模型评价报告 - 6变量改进版")
    report.append("=" * 90)
    report.append("")
    
    # 1. 基本信息
    report.append("【1】基本信息")
    report.append("-" * 90)
    report.append(f"样本量:          {n_samples:6d}")
    report.append(f"变量数:          {n_vars:6d}")
    report.append(f"样本/变量比:     {n_samples/n_vars:6.2f}:1  (建议 ≥3:1，目前{'✓' if n_samples/n_vars >= 3 else '✗'})")
    report.append(f"因子数:          {n_factors}  (特征值>1自动确定)")
    report.append("")
    
    # 2. KMO检验
    report.append("【2】KMO (Kaiser-Meyer-Olkin) 检验")
    report.append("-" * 90)
    report.append(f"整体KMO值:       {kmo_overall:.4f}")
    
    if kmo_overall >= 0.9:
        kmo_grade = "优秀 (Excellent)"
        kmo_icon = "★★★"
    elif kmo_overall >= 0.8:
        kmo_grade = "很好 (Meritorious)"
        kmo_icon = "★★"
    elif kmo_overall >= 0.7:
        kmo_grade = "可以 (Middling)"
        kmo_icon = "★"
    elif kmo_overall >= 0.6:
        kmo_grade = "一般 (Mediocre)"
        kmo_icon = "○"
    else:
        kmo_grade = "勉强 (Miserable)"
        kmo_icon = "△"
    
    report.append(f"解释等级:        {kmo_icon} {kmo_grade}")
    report.append("")
    report.append("各变量的KMO值:")
    for i, var in enumerate(factor_vars):
        report.append(f"  {var:40s}  {kmo_vars[i]:.4f}")
    report.append("")
    
    # 3. Bartlett检验
    report.append("【3】Bartlett 球形检验")
    report.append("-" * 90)
    report.append(f"卡方统计量：     {chi_sq:12.4f}")
    report.append(f"自由度：         {int(df):12d}")
    report.append(f"p值：            {p_value:.4e}")
    report.append(f"结论：           {'✓ 高度显著，数据适合因子分析' if p_value < 0.001 else '○ 显著，适合因子分析' if p_value < 0.05 else '✗ 不显著'}")
    report.append("")
    
    # 4. 共同度
    report.append("【4】共同度分析 (Communalities)")
    report.append("-" * 90)
    
    for i, var in enumerate(factor_vars):
        report.append(f"  {var:40s}  {communalities[i]:.4f}  ({communalities[i]*100:5.1f}%)")
    
    report.append("")
    report.append(f"平均共同度:      {communalities.mean():.4f}")
    report.append(f"共同度范围:      {communalities.min():.4f} ~ {communalities.max():.4f}")
    if communalities.mean() > 0.6:
        report.append(f"评价:            ★★ 优秀 (平均 {communalities.mean():.3f} > 0.6)")
    elif communalities.mean() > 0.5:
        report.append(f"评价:            ★  可接受 (平均 {communalities.mean():.3f})")
    else:
        report.append(f"评价:            △ 一般 (平均 {communalities.mean():.3f})")
    report.append("")
    
    # 5. 因子解释方差
    report.append("【5】因子解释方差")
    report.append("-" * 90)
    report.append("")
    report.append(f"{'因子':<10} {'方差贡献':<12} {'贡献率%':<12} {'累计贡献率%':<12}")
    report.append("-" * 50)
    for i in range(n_factors):
        report.append(f"Factor{i+1:<5} {factor_variance[i]:>11.4f}  {var_explained[i]:>10.2f}%  {cumsum_var[i]:>10.2f}%")
    
    report.append("")
    report.append(f"{n_factors}个因子累计解释方差: {cumsum_var[-1]:.2f}%")
    if cumsum_var[-1] > 70:
        report.append(f"评价: ★★ 优秀 (>70%)")
    elif cumsum_var[-1] > 60:
        report.append(f"评价: ★  良好 (60-70%)")
    else:
        report.append(f"评价: ○ 可接受")
    report.append("")
    
    # 6. 因子载荷质量
    report.append("【6】因子载荷质量")
    report.append("-" * 90)
    
    abs_loadings = np.abs(loadings)
    cnt_05 = (abs_loadings > 0.5).sum()
    cnt_06 = (abs_loadings > 0.6).sum()
    total_loads = n_vars * n_factors
    
    report.append(f"高质量载荷 (|λ|>0.5): {cnt_05:3d}/{total_loads}  {cnt_05/total_loads*100:5.1f}%")
    report.append(f"优质载荷   (|λ|>0.6): {cnt_06:3d}/{total_loads}  {cnt_06/total_loads*100:5.1f}%")
    
    if cnt_05/total_loads > 0.5:
        report.append(f"评价: ★★ 优秀")
    elif cnt_05/total_loads > 0.4:
        report.append(f"评价: ★  良好")
    else:
        report.append(f"评价: ○ 一般")
    report.append("")
    
    # 7. 综合评价
    report.append("【7】综合评价")
    report.append("=" * 90)
    
    score = 0
    details = []
    
    if kmo_overall >= 0.7:
        score += 2
        details.append(f"✓ KMO={kmo_overall:.3f} (>0.7，优秀)")
    elif kmo_overall >= 0.6:
        score += 1
        details.append(f"○ KMO={kmo_overall:.3f} (0.6-0.7，可接受)")
    else:
        details.append(f"△ KMO={kmo_overall:.3f}")
    
    if p_value < 0.001:
        score += 2
        details.append(f"✓ Bartlett: p<0.001 (极显著)")
    else:
        details.append(f"○ Bartlett: 显著")
    
    if communalities.mean() > 0.6:
        score += 2
        details.append(f"✓ 共同度={communalities.mean():.3f} (>0.6，优秀)")
    elif communalities.mean() > 0.5:
        score += 1
        details.append(f"○ 共同度={communalities.mean():.3f} (平均)")
    
    if cumsum_var[-1] > 70:
        score += 2
        details.append(f"✓ 方差={cumsum_var[-1]:.1f}% (>70%，优秀)")
    elif cumsum_var[-1] > 60:
        score += 1
        details.append(f"○ 方差={cumsum_var[-1]:.1f}% (60-70%)")
    else:
        details.append(f"○ 方差={cumsum_var[-1]:.1f}%")
    
    report.append("")
    for detail in details:
        report.append(detail)
    
    report.append("")
    report.append(f"综合评分: {score}/8 分")
    report.append("")
    
    if score >= 7:
        report.append("【评级】 ★★★ 优秀模型")
        report.append("✓ 可以放心用于后续分析和论文呈现")
    elif score >= 5:
        report.append("【评级】 ★★ 良好模型")
        report.append("✓ 适合后续使用")
    else:
        report.append("【评级】 ★ 可接受")
    
    report.append("")
    report.append("=" * 90)
    
    report_text = "\n".join(report)
    
    with open('data/derived/factor_evaluation_6vars.txt', 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(report_text)

if __name__ == '__main__':
    evaluate_fa_6vars()
