#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用训练好的模型对下一个交易日进行预测
"""

import pickle
import pandas as pd
from pathlib import Path
import qlib

# 初始化qlib
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region="cn")

def load_latest_prediction():
    """
    加载最新的预测数据
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
    
    # 直接加载预测数据
    pred_file = latest_recorder / "artifacts" / "pred.pkl"
    
    if not pred_file.exists():
        raise FileNotFoundError(f"Prediction file not found: {pred_file}")
    
    pred = pickle.load(open(pred_file, 'rb'))
    print(f"Prediction data shape: {pred.shape}")
    
    return pred

def main():
    """
    主函数
    """
    # 加载最新的预测数据
    pred = load_latest_prediction()
    
    # 获取预测的日期范围
    dates = pred.index.get_level_values('datetime').unique()
    last_date = dates.max()
    second_last_date = sorted(dates)[-2] if len(dates) >= 2 else dates.min()
    
    print(f"\nLast prediction date: {last_date}")
    print(f"Second last prediction date: {second_last_date}")
    print(f"Total prediction dates: {len(dates)}")
    print(f"Date range: {dates[0]} to {last_date}")
    
    # 选择要显示的日期
    target_date = last_date
    
    # 获取所有股票
    stocks = pred.index.get_level_values('instrument').unique()
    print(f"Total stocks: {len(stocks)}")
    
    # 提取指定日期的预测结果
    target_day_pred = pred.loc[target_date].copy()
    
    # 重置索引并重命名列
    target_day_pred = target_day_pred.reset_index()
    target_day_pred.columns = ['stock', 'prediction']
    
    # 添加日期和排名
    target_day_pred['date'] = target_date
    target_day_pred['rank'] = target_day_pred['prediction'].rank(ascending=False).round(2)
    target_day_pred['prediction'] = target_day_pred['prediction'].round(2)
    
    # 按预测分数排序
    target_day_pred = target_day_pred.sort_values('prediction', ascending=False)
    
    # 保存预测结果
    output_file = f"prediction_{target_date.strftime('%Y-%m-%d')}.csv"
    target_day_pred.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\nPrediction results saved to: {output_file}")
    print(f"Total predictions: {len(target_day_pred)}")
    print(f"Prediction range: {target_day_pred['prediction'].min():.2f} to {target_day_pred['prediction'].max():.2f}")


if __name__ == "__main__":
    main()
