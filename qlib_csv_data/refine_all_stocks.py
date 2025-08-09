import os
import re
import pandas as pd
from tqdm import tqdm

root_dir = "./qlib_csv_data"
csv_files = os.listdir(root_dir)

for csv_file in tqdm(csv_files):
    if csv_file.endswith(".csv"):
        df = pd.read_csv(os.path.join(root_dir, csv_file))
        # 追加两行, 第一列是股票代码, 第二列是日期，其他均为空
        # 获取股票代码和日期
        if not df.empty:
            stock_code = df.iloc[0, 0]
            date1 = "2025-08-04"
            date2 = "2025-08-05"
            # 构造两行数据
            row1 = [stock_code, date1] + [None] * (df.shape[1] - 2)
            row2 = [stock_code, date2] + [None] * (df.shape[1] - 2)
            # 追加到 DataFrame
            df = pd.concat([df, pd.DataFrame([row1, row2], columns=df.columns)], ignore_index=True)
            # 保存回原文件
            df.to_csv(os.path.join(root_dir, csv_file), index=False)

exit()

csv_names = [f[:-4] for f in csv_files if f.endswith(".csv")]

filtered_csv_names = []
for csv_name in csv_names:
    # number = csv_name[2:]
    # if number.startswith("688") or number.startswith("300") or number.startswith("301") or 
    #     continue
    name_rule_re='^(?!BJ[0-9]+)(?!SZ30[0-9]+)(?!SH688[0-9]+).*$'
    if re.match(name_rule_re, csv_name):
        print(csv_name)
        filtered_csv_names.append(csv_name)

csv_names = filtered_csv_names


print(f"处理的股票数量: {len(csv_names)}")
# import ipdb; ipdb.set_trace()

refine_all_txt = []
origin_all_txt_path = os.path.expanduser("~/.qlib/qlib_data/cn_data/instruments/all.txt")

# 检查源文件是否存在
if not os.path.exists(origin_all_txt_path):
    print(f"错误：源文件不存在: {origin_all_txt_path}")
    print("请确保 qlib 数据已正确安装")
    exit(1)

with open(origin_all_txt_path, "r") as f:
    for line in f:
        stock_name = line[:len("SZ399965")]
        print(stock_name)
        if stock_name not in csv_names:
            continue
        refine_all_txt.append(line)

refine_all_txt_path = os.path.expanduser("~/.qlib/qlib_data/cn_data/instruments/refine_all.txt")

# 确保输出目录存在
output_dir = os.path.dirname(refine_all_txt_path)
os.makedirs(output_dir, exist_ok=True)

with open(refine_all_txt_path, "w") as f:
    for line in refine_all_txt:
        f.write(line)

print(f"处理完成！共处理了 {len(refine_all_txt)} 只股票")
print(f"输出文件：{refine_all_txt_path}")