import qlib
from qlib.data import D
from qlib.constant import REG_CN
import pandas as pd

# 初始化 Qlib
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region=REG_CN)

# 获取所有股票代码
stocks = D.instruments(market="all")
stock_list = D.list_instruments(instruments=stocks, as_list=True)

result = []

def month_range(start, end):
    # 生成[start, end]之间所有月份（格式：YYYY-MM）
    months = []
    cur = pd.Timestamp(start.replace(day=1))
    end = pd.Timestamp(end.replace(day=1))
    while cur <= end:
        months.append(cur.strftime("%Y-%m"))
        # 下一个月
        if cur.month == 12:
            cur = pd.Timestamp(year=cur.year+1, month=1, day=1)
        else:
            cur = pd.Timestamp(year=cur.year, month=cur.month+1, day=1)
    return months

for stock in stock_list:
    df = D.features([stock], fields=["$close"])
    if df.empty:
        continue
    dates = df.index.get_level_values("datetime")
    start = dates.min()
    end = dates.max()
    all_months = set(month_range(start, end))
    months = set(d.strftime("%Y-%m") for d in dates)
    missing_months = sorted(all_months - months)
    if missing_months:
        for m in missing_months:
            result.append((stock, m))

# 只输出有缺失月份的股票及其缺失月份
missing_df = pd.DataFrame(result, columns=["stock", "missing_month"])
# 忽略2006-04的缺失
missing_df = missing_df[missing_df['missing_month'] != '2006-04']
print(missing_df)
missing_df.to_csv("stock_missing_months.csv", index=False)