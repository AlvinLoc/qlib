#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成两种数据集文件
1. csi1000-online-all.txt（从all.txt或csi1000.txt生成，包含所有未退市的股票）
2. csi1000-online-300.txt（从csi1000-online-all.txt随机抽取300只，必须包含SH000300）
"""

import os
import random

def get_latest_date(stocks_data):
    """
    获取所有股票中最新的日期
    """
    latest_date = None
    for stock_code, start_date, end_date in stocks_data:
        if latest_date is None or end_date > latest_date:
            latest_date = end_date
    return latest_date

def read_stocks_file(file_path):
    """
    读取股票文件，返回股票数据列表
    每个元素是 (stock_code, start_date, end_date)
    """
    stocks_data = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 3:
                        stock_code = parts[0]
                        start_date = parts[1]
                        end_date = parts[2]
                        stocks_data.append((stock_code, start_date, end_date))
    return stocks_data

def generate_csi1000_online_all():
    """
    从all.txt或csi1000.txt中获取所有未退市的股票，保存为csi1000-online-all
    """
    all_file = os.path.expanduser('~/.qlib/qlib_data/cn_data/instruments/all.txt')
    csi1000_file = os.path.expanduser('~/.qlib/qlib_data/cn_data/instruments/csi1000.txt')
    output_file = os.path.expanduser('~/.qlib/qlib_data/cn_data/instruments/csi1000-online-all.txt')
    
    print(f"Reading stocks from {all_file} or {csi1000_file}")
    print(f"Output will be saved to: {output_file}")
    
    # 优先使用all.txt，如果不存在则使用csi1000.txt
    stocks_data = []
    if os.path.exists(all_file):
        stocks_data = read_stocks_file(all_file)
        print(f"Using all.txt: {len(stocks_data)} stocks found")
    elif os.path.exists(csi1000_file):
        stocks_data = read_stocks_file(csi1000_file)
        print(f"Using csi1000.txt: {len(stocks_data)} stocks found")
    else:
        print(f"Warning: Neither {all_file} nor {csi1000_file} exists")
        return None
    
    # 获取最新日期
    latest_date = get_latest_date(stocks_data)
    print(f"Latest date in data: {latest_date}")
    
    # 筛选出未退市的股票（结束日期等于最新日期），保留完整信息
    active_stocks_data = []
    for stock_code, start_date, end_date in stocks_data:
        if end_date == latest_date:
            active_stocks_data.append((stock_code, start_date, end_date))
    
    print(f"Active stocks (not delisted): {len(active_stocks_data)}")
    
    # 删除旧的输出文件（如果存在）
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Removed old output file: {output_file}")
    
    # 保存所有未退市的股票（格式：股票代码\t开始日期\t结束日期）
    with open(output_file, 'w', encoding='utf-8') as f:
        for stock_code, start_date, end_date in sorted(active_stocks_data):
            f.write(f"{stock_code}\t{start_date}\t{end_date}\n")
    
    print(f"\nFilter completed!")
    print(f"Total stocks saved: {len(active_stocks_data)}")
    print(f"\ncsi1000-online-all stock dataset has been saved to: {output_file}")
    
    return active_stocks_data

def generate_csi1000_online_300(active_stocks_data):
    """
    从csi1000-online-all.txt中随机抽取300只股票（必须包含SH000300），保存为csi1000-online-300
    """
    input_file = os.path.expanduser('~/.qlib/qlib_data/cn_data/instruments/csi1000-online-all.txt')
    output_file = os.path.expanduser('~/.qlib/qlib_data/cn_data/instruments/csi1000-online-300.txt')
    
    print(f"Reading stocks from {input_file}")
    print(f"Output will be saved to: {output_file}")
    
    # 确保SH000300在列表中
    sh000300 = 'SH000300'
    sh000300_data = None
    for stock_code, start_date, end_date in active_stocks_data:
        if stock_code == sh000300:
            sh000300_data = (stock_code, start_date, end_date)
            break
    
    if sh000300_data is None:
        print(f"Warning: {sh000300} not found in active stocks list")
    else:
        print(f"{sh000300} found in active stocks list")
    
    # 随机抽取300只股票，必须包含SH000300
    if len(active_stocks_data) >= 300:
        # 先移除SH000300（如果存在）
        stocks_without_sh000300 = [s for s in active_stocks_data if s[0] != sh000300]
        # 从剩余股票中随机抽取299只
        sampled_stocks = random.sample(stocks_without_sh000300, 299)
        # 添加SH000300
        if sh000300_data:
            sampled_stocks.append(sh000300_data)
        # 打乱顺序
        random.shuffle(sampled_stocks)
    else:
        # 如果股票总数不足300只，则全部使用
        sampled_stocks = active_stocks_data.copy()
        # 确保SH000300在列表中
        if sh000300_data and not any(s[0] == sh000300 for s in sampled_stocks):
            sampled_stocks.append(sh000300_data)
    
    # 删除旧的输出文件（如果存在）
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Removed old output file: {output_file}")
    
    # 保存随机抽取的300只股票（格式：股票代码\t开始日期\t结束日期）
    with open(output_file, 'w', encoding='utf-8') as f:
        for stock_code, start_date, end_date in sampled_stocks:
            f.write(f"{stock_code}\t{start_date}\t{end_date}\n")
    
    print(f"\nFilter completed!")
    print(f"Total stocks saved: {len(sampled_stocks)}")
    print(f"Contains SH000300: {sh000300 in [s[0] for s in sampled_stocks]}")
    print(f"\ncsi1000-online-300 stock dataset has been saved to: {output_file}")

def main():
    """
    主函数
    """
    print("=== Generating 2 Stock Datasets ===\n")
    
    # 生成csi1000-online-all.txt
    print("\n1. Generating csi1000-online-all.txt...")
    active_stocks_data = generate_csi1000_online_all()
    
    if active_stocks_data:
        # 生成csi1000-online-300.txt
        print("\n2. Generating csi1000-online-300.txt...")
        generate_csi1000_online_300(active_stocks_data)
        
        print("\n=== All 2 datasets generated successfully! ===")
    else:
        print("\n=== Failed to generate datasets: no active stocks found ===")

if __name__ == "__main__":
    main()
