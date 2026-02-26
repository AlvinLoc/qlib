#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成三种数据集文件
1. csi1000-online-all.txt（从csi1000.txt生成）
2. csi1000-online-300.txt（从csi1000.txt取前300只）
3. csi1000-online-mini.txt（从csi1000.txt取前100只）
"""

import os

def generate_csi1000_online_all():
    """
    从csi1000.txt中获取所有未退市的股票，保存为csi1000-online-all
    """
    input_file = '/Users/alvin/.qlib/qlib_data/cn_data/instruments/csi1000.txt'
    output_file = '/Users/alvin/.qlib/qlib_data/cn_data/instruments/csi1000-online-all.txt'
    
    print(f"Reading stocks from {input_file}")
    print(f"Output will be saved to: {output_file}")
    
    # 读取csi1000.txt中的所有股票
    all_stocks = set()
    if os.path.exists(input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    stock_code = line.strip()
                    all_stocks.add(stock_code)
        
        print(f"Total stocks in csi1000.txt: {len(all_stocks)}")
    else:
        print(f"Warning: {input_file} does not exist")
        all_stocks = set()
    
    # 删除旧的输出文件（如果存在）
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Removed old output file: {output_file}")
    
    # 保存所有股票
    with open(output_file, 'w', encoding='utf-8') as f:
        for stock in sorted(all_stocks):
            f.write(f"{stock}\n")
    
    print(f"\nFilter completed!")
    print(f"Total stocks saved: {len(all_stocks)}")
    print(f"\ncsi1000-online-all stock dataset has been saved to: {output_file}")

def generate_csi1000_online_300():
    """
    从csi1000.txt中取前300只股票，保存为csi1000-online-300
    """
    input_file = '/Users/alvin/.qlib/qlib_data/cn_data/instruments/csi1000.txt'
    output_file = '/Users/alvin/.qlib/qlib_data/cn_data/instruments/csi1000-online-300.txt'
    
    print(f"Reading stocks from {input_file}")
    print(f"Output will be saved to: {output_file}")
    
    # 读取csi1000.txt中的股票
    stocks = []
    if os.path.exists(input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    stock_code = line.strip()
                    stocks.append(stock_code)
        
        print(f"Total stocks in csi1000.txt: {len(stocks)}")
    else:
        print(f"Warning: {input_file} does not exist")
        stocks = []
    
    # 取前300只股票
    stocks_300 = stocks[:300] if len(stocks) >= 300 else stocks
    
    # 删除旧的输出文件（如果存在）
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Removed old output file: {output_file}")
    
    # 保存前300只股票
    with open(output_file, 'w', encoding='utf-8') as f:
        for stock in stocks_300:
            f.write(f"{stock}\n")
    
    print(f"\nFilter completed!")
    print(f"Total stocks saved: {len(stocks_300)}")
    print(f"\ncsi1000-online-300 stock dataset has been saved to: {output_file}")

def generate_csi1000_online_mini():
    """
    从csi1000.txt中取前100只股票，保存为csi1000-online-mini
    """
    input_file = '/Users/alvin/.qlib/qlib_data/cn_data/instruments/csi1000.txt'
    output_file = '/Users/alvin/.qlib/qlib_data/cn_data/instruments/csi1000-online-mini.txt'
    
    print(f"Reading stocks from {input_file}")
    print(f"Output will be saved to: {output_file}")
    
    # 读取csi1000.txt中的股票
    stocks = []
    if os.path.exists(input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    stock_code = line.strip()
                    stocks.append(stock_code)
        
        print(f"Total stocks in csi1000.txt: {len(stocks)}")
    else:
        print(f"Warning: {input_file} does not exist")
        stocks = []
    
    # 取前100只股票
    stocks_100 = stocks[:100] if len(stocks) >= 100 else stocks
    
    # 删除旧的输出文件（如果存在）
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Removed old output file: {output_file}")
    
    # 保存前100只股票
    with open(output_file, 'w', encoding='utf-8') as f:
        for stock in stocks_100:
            f.write(f"{stock}\n")
    
    print(f"\nFilter completed!")
    print(f"Total stocks saved: {len(stocks_100)}")
    print(f"\ncsi1000-online-mini stock dataset has been saved to: {output_file}")

def main():
    """
    主函数
    """
    print("=== Generating 3 Stock Datasets ===\n")
    
    # 生成csi1000-online-all.txt
    print("\n1. Generating csi1000-online-all.txt...")
    generate_csi1000_online_all()
    
    # 生成csi1000-online-300.txt
    print("\n2. Generating csi1000-online-300.txt...")
    generate_csi1000_online_300()
    
    # 生成csi1000-online-mini.txt
    print("\n3. Generating csi1000-online-mini.txt...")
    generate_csi1000_online_mini()
    
    print("\n=== All 3 datasets generated successfully! ===")

if __name__ == "__main__":
    main()
