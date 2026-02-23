#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析模型预测结果和各种指标，以及相应的真值，结果保存成csv
"""

import pickle
import pandas as pd
import os
import sys
from pathlib import Path

def load_latest_experiment():
    """
    加载最新的实验结果
    """
    mlruns_dir = Path("mlruns")
    
    # 找到最新的实验目录
    experiments = sorted([d for d in mlruns_dir.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime)
    if not experiments:
        raise FileNotFoundError("No experiments found in mlruns directory")
    
    latest_exp = experiments[-1]
    print(f"Latest experiment: {latest_exp.name}")
    
    # 找到最新的recorder（按修改时间排序）
    recorders = [d for d in latest_exp.iterdir() if d.is_dir()]
    if not recorders:
        raise FileNotFoundError(f"No recorders found in {latest_exp}")
    
    # 按修改时间排序，选择最新的
    latest_recorder = max(recorders, key=lambda x: x.stat().st_mtime)
    print(f"Latest recorder: {latest_recorder.name}")
    
    artifacts_dir = latest_recorder / "artifacts"
    return artifacts_dir

def analyze_predictions(artifacts_dir, last_n_days=None):
    """
    分析预测结果和指标
    """
    print(f"\nAnalyzing predictions...")
    
    # 读取预测结果
    pred_file = artifacts_dir / "pred.pkl"
    if not pred_file.exists():
        raise FileNotFoundError(f"Prediction file not found: {pred_file}")
    
    pred = pickle.load(open(pred_file, 'rb'))
    print(f"Prediction data shape: {pred.shape}")
    
    # 读取标签数据
    label_file = artifacts_dir / "label.pkl"
    if not label_file.exists():
        raise FileNotFoundError(f"Label file not found: {label_file}")
    
    label = pickle.load(open(label_file, 'rb'))
    print(f"Label data shape: {label.shape}")
    
    # 读取IC指标
    ic_file = artifacts_dir / "sig_analysis" / "ic.pkl"
    if ic_file.exists():
        ic = pickle.load(open(ic_file, 'rb'))
        print(f"IC data available")
    else:
        ic = None
        print("IC data not found")
    
    # 读取Rank IC指标
    ric_file = artifacts_dir / "sig_analysis" / "ric.pkl"
    if ric_file.exists():
        ric = pickle.load(open(ric_file, 'rb'))
        print(f"Rank IC data available")
    else:
        ric = None
        print("Rank IC data not found")
    
    # 如果指定了last_n_days，则只分析最后几天
    if last_n_days is not None:
        # 分析最后几天的数据
        all_dates = pred.index.get_level_values('datetime').unique()
        last_dates = sorted(all_dates)[-last_n_days:]
        print(f"\nLast {last_n_days} dates: {last_dates}")
        
        # 提取最后几天的数据
        pred_last = pred.loc[last_dates]
        label_last = label.loc[last_dates]
        
        # 合并预测和标签
        results = []
        for date in last_dates:
            date_pred = pred_last.loc[date].copy()
            date_label = label_last.loc[date].copy()
            
            # 添加日期列
            date_pred['date'] = date
            date_label['date'] = date
            
            # 重命名列 - 检查实际的列名
            pred_col = date_pred.columns[0]
            label_col = date_label.columns[0]
            
            date_pred = date_pred.reset_index().rename(columns={'instrument': 'stock', pred_col: 'prediction'})
            date_label = date_label.reset_index().rename(columns={'instrument': 'stock', label_col: 'label'})
            
            # 合并
            merged = pd.merge(date_pred, date_label, on=['date', 'stock'], how='outer')
            results.append(merged)
        
        # 合并所有日期的结果
        final_df = pd.concat(results, ignore_index=True)
    else:
        # 分析所有数据
        all_dates = pred.index.get_level_values('datetime').unique()
        print(f"\nTotal dates: {len(all_dates)}")
        print(f"Date range: {all_dates[0]} to {all_dates[-1]}")
        
        # 提取所有数据
        pred_all = pred.copy()
        label_all = label.copy()
        
        # 合并预测和标签
        results = []
        for date in all_dates:
            date_pred = pred_all.loc[date].copy()
            date_label = label_all.loc[date].copy()
            
            # 添加日期列
            date_pred['date'] = date
            date_label['date'] = date
            
            # 重命名列 - 检查实际的列名
            pred_col = date_pred.columns[0]
            label_col = date_label.columns[0]
            
            date_pred = date_pred.reset_index().rename(columns={'instrument': 'stock', pred_col: 'prediction'})
            date_label = date_label.reset_index().rename(columns={'instrument': 'stock', label_col: 'label'})
            
            # 合并
            merged = pd.merge(date_pred, date_label, on=['date', 'stock'], how='outer')
            results.append(merged)
        
        # 合并所有日期的结果
        final_df = pd.concat(results, ignore_index=True)
    
    # 添加IC和Rank IC信息
    if ic is not None:
        ic_values = []
        for date in final_df['date'].unique():
            if date in ic.index:
                ic_values.append({'date': date, 'IC': ic[date]})
        ic_df = pd.DataFrame(ic_values)
        final_df = pd.merge(final_df, ic_df, on='date', how='left')
    
    if ric is not None:
        ric_values = []
        for date in final_df['date'].unique():
            if date in ric.index:
                ric_values.append({'date': date, 'Rank IC': ric[date]})
        ric_df = pd.DataFrame(ric_values)
        final_df = pd.merge(final_df, ric_df, on='date', how='left')
    
    # 计算预测误差
    final_df['prediction_error'] = final_df['prediction'] - final_df['label']
    final_df['abs_error'] = abs(final_df['prediction_error'])
    
    # 按日期和预测分数排序
    final_df = final_df.sort_values(['date', 'prediction'], ascending=[True, False])
    
    # 添加排名
    final_df['rank'] = final_df.groupby('date')['prediction'].rank(ascending=False)
    
    return final_df

def save_to_csv(df, output_file):
    """
    保存结果到CSV文件
    """
    # 将所有小数列格式化为2位小数
    for col in df.columns:
        if df[col].dtype in ['float64', 'float32']:
            df[col] = df[col].round(2)
    
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\nResults saved to: {output_file}")
    print(f"Total rows: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")

def main():
    """
    主函数
    """
    import sys
    
    # 加载最新的实验结果
    artifacts_dir = load_latest_experiment()
    
    # 检查命令行参数，默认分析最后5天
    last_n_days = 5
    if len(sys.argv) > 1:
        try:
            last_n_days = int(sys.argv[1])
            print(f"Analyzing last {last_n_days} days as specified")
        except ValueError:
            print("Invalid argument. Usage: python analyze_predictions.py [days]")
            print("Default: analyze last 5 days")
    
    # 分析预测结果
    results_df = analyze_predictions(artifacts_dir, last_n_days)
    
    # 保存到CSV
    if last_n_days is None:
        output_file = "prediction_analysis_all.csv"
    else:
        output_file = f"prediction_analysis_last_{last_n_days}_days.csv"
    
    save_to_csv(results_df, output_file)
    
    # 显示统计信息
    print("\n=== Statistics ===")
    print(f"Total predictions: {len(results_df)}")
    print(f"Dates covered: {results_df['date'].nunique()}")
    print(f"Stocks covered: {results_df['stock'].nunique()}")
    print(f"\nPrediction statistics:")
    print(results_df[['prediction', 'label', 'prediction_error', 'abs_error']].describe())
    
    # 显示最后一天所有股票的排名
    print("\n=== Last Day All Stock Rankings ===")
    last_date = results_df['date'].max()
    last_day_df = results_df[results_df['date'] == last_date]
    last_day_ranked = last_day_df.sort_values('prediction', ascending=False)
    print(f"Total stocks on {last_date}: {len(last_day_ranked)}")
    print(f"Prediction range: {last_day_ranked['prediction'].min():.2f} to {last_day_ranked['prediction'].max():.2f}")
    print(f"\nTop 10 stocks by prediction:")
    print(last_day_ranked[['stock', 'prediction', 'label', 'rank']].head(10).to_string(index=False))
    print(f"\nBottom 10 stocks by prediction:")
    print(last_day_ranked[['stock', 'prediction', 'label', 'rank']].tail(10).to_string(index=False))

if __name__ == "__main__":
    main()
