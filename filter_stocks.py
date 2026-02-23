#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从csi1000-online中取前300只股票，保存为csi1000-online-300
"""

import os

# 输入文件路径
input_file = os.path.expanduser('~/.qlib/qlib_data/cn_data/instruments/csi1000-online.txt')
# 输出文件路径
output_file = os.path.expanduser('~/.qlib/qlib_data/cn_data/instruments/csi1000-online-300.txt')

print(f"Reading stocks from {input_file}")
print(f"Output will be saved to {output_file}")

# 读取csi1000-online股票
with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 取前300只股票
stocks_300 = lines[:300]

# 删除旧的输出文件（如果存在）
if os.path.exists(output_file):
    os.remove(output_file)
    print(f"Removed old output file: {output_file}")

# 保存前300只股票
with open(output_file, 'w', encoding='utf-8') as f:
    f.writelines(stocks_300)

print(f"\nFilter completed!")
print(f"Total csi1000-online stocks: {len(lines)}")
print(f"Selected stocks (first 300): {len(stocks_300)}")
print(f"\ncsi1000-online-300 stock dataset has been saved to: {output_file}")
