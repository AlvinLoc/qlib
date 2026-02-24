#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从all.txt中获取所有未退市的股票，保存为csi1000-online-all
"""

import os

# 输入文件路径
all_file = os.path.expanduser('~/.qlib/qlib_data/cn_data/instruments/all.txt')
# 输出文件路径
output_file = os.path.expanduser('~/.qlib/qlib_data/cn_data/instruments/csi1000-online-all.txt')

print(f"Reading stocks from {all_file}")
print(f"Output will be saved to: {output_file}")

# 读取all.txt中的所有股票
all_stocks = set()
if os.path.exists(all_file):
    with open(all_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                stock_code = line.strip().split('\t')[0]
                all_stocks.add(stock_code)
    
    print(f"Total stocks in all.txt: {len(all_stocks)}")
else:
    print(f"Warning: {all_file} does not exist")
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
