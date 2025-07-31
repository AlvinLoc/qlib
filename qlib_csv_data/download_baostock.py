import asyncio
import baostock as bs
import pandas as pd
import os
import time
import datetime

DEBUG_MODE = False


# 登录 baostock 数据接口
def login_baostock():
    """
    登录 baostock 数据服务
    返回: True 表示登录成功，False 表示登录失败
    """
    lg = bs.login()
    if lg.error_code != "0":
        print(f"登录失败，错误代码: {lg.error_code}，错误信息: {lg.error_msg}")
        return False
    return True


# 获取所有股票代码
def get_all_stock_codes():
    """
    获取当前交易日所有可交易的股票代码列表
    返回: 股票代码列表，格式如 ['sh.600000', 'sz.000001', ...]
    """
    today = datetime.date.today().strftime("%Y-%m-%d")
    now_time = datetime.datetime.now().strftime("%H:%M:%S")
    if now_time < "04:00:00":
        today = (
            datetime.datetime.strptime(today, "%Y-%m-%d") - datetime.timedelta(days=1)
        ).strftime("%Y-%m-%d")
    rs = bs.query_all_stock(day=today)
    if rs.error_code != "0":
        print(f"获取股票列表失败，错误代码: {rs.error_code}，错误信息: {rs.error_msg}")
        return []
    data_list = []
    while (rs.error_code == "0") & rs.next():
        data_list.append(rs.get_row_data())
    df = pd.DataFrame(data_list, columns=rs.fields)
    # 只保留交易状态为 '1'（正常交易）的股票
    stock_codes = df[df["tradeStatus"] == "1"]["code"].tolist()
    if DEBUG_MODE:
        stock_codes = stock_codes[:10]
    return stock_codes


# 下载单只股票数据
def download_stock_data(stock_code, start_date, end_date):
    """
    下载指定股票在指定时间范围内的历史K线数据

    参数:
        stock_code: 股票代码，如 'sh.600000'
        start_date: 开始日期，格式 'YYYY-MM-DD'
        end_date: 结束日期，格式 'YYYY-MM-DD'

    返回: DataFrame 包含股票历史数据，失败时返回 None
    """
    rs = bs.query_history_k_data_plus(
        stock_code,
        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
        start_date=start_date,
        end_date=end_date,
        frequency="d",  # 日线数据
        adjustflag="3",  # 后复权
    )

    if rs.error_code != "0":
        print(
            f"下载 {stock_code} 数据失败，错误代码: {rs.error_code}，错误信息: {rs.error_msg}"
        )
        return None
    data_list = []
    while (rs.error_code == "0") & rs.next():
        data_list.append(rs.get_row_data())
    df = pd.DataFrame(data_list, columns=rs.fields)
    return df


# 转换数据格式为 qlib 需要的格式
def convert_to_qlib_format(df, stock_code):
    """
    将 baostock 数据转换为 qlib 需要的格式

    参数:
        df: baostock 原始数据 DataFrame
        stock_code: 股票代码

    返回: 转换后的 DataFrame，包含 qlib 需要的字段
    """
    if df is None or df.empty:
        return None

    # 转换股票代码格式：sh.600000 -> SH600000
    qlib_stock_code = stock_code.upper().replace(".", "")

    # 创建 qlib 格式的数据
    qlib_df = pd.DataFrame(
        {
            "symbol": qlib_stock_code,
            "date": pd.to_datetime(df["date"]),
            "open": pd.to_numeric(df["open"], errors="coerce"),
            "high": pd.to_numeric(df["high"], errors="coerce"),
            "low": pd.to_numeric(df["low"], errors="coerce"),
            "close": pd.to_numeric(df["close"], errors="coerce"),
            "volume": pd.to_numeric(df["volume"], errors="coerce"),
            "amount": pd.to_numeric(df["amount"], errors="coerce"),
            "factor": 1.0,  # 后复权数据，factor 设为 1.0
        }
    )

    # 过滤掉无效数据
    qlib_df = qlib_df.dropna(subset=["open", "high", "low", "close", "volume"])

    return qlib_df


# 批量下载所有股票数据（qlib 格式）
def download_all_stocks_qlib_format(start_date, end_date, output_dir="qlib_csv_data"):
    """
    批量下载所有股票的历史数据，保存为 qlib 需要的 CSV 格式

    参数:
        start_date: 开始日期，格式 'YYYY-MM-DD'
        end_date: 结束日期，格式 'YYYY-MM-DD'
        output_dir: 输出目录，默认为 'qlib_csv_data'

    功能:
        1. 登录 baostock 服务
        2. 获取所有可交易的股票代码
        3. 为每只股票下载历史数据并转换为 qlib 格式
        4. 保存为 CSV 文件，文件名为股票代码
        5. 最后注销登录
    """
    # 登录 baostock 服务
    if not login_baostock():
        return

    # 创建保存数据的目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)

    # 获取所有可交易的股票代码
    stock_codes = get_all_stock_codes()
    print(f"获取到 {len(stock_codes)} 只股票")

    # 遍历每只股票进行数据下载
    for i, stock_code in enumerate(stock_codes):
        print(f"正在处理第 {i + 1}/{len(stock_codes)} 只股票: {stock_code}")

        # 下载股票数据
        df = download_stock_data(stock_code, start_date, end_date)

        if df is not None and not df.empty:
            # 转换为 qlib 格式
            qlib_df = convert_to_qlib_format(df, stock_code)

            if qlib_df is not None and not qlib_df.empty:
                # 保存为 CSV 文件，文件名为股票代码
                qlib_stock_code = stock_code.upper().replace(".", "")
                csv_filename = f"{qlib_stock_code}.csv"
                csv_path = os.path.join(output_dir, csv_filename)
                if os.path.exists(csv_path):
                    print(f"文件 {csv_path} 已存在，跳过")
                    continue

                # 保存 CSV 文件
                qlib_df.to_csv(csv_path, index=False)
                print(f"已保存 {csv_filename}，数据条数: {len(qlib_df)}")
            else:
                print(f"股票 {stock_code} 数据为空或转换失败")
        else:
            print(f"股票 {stock_code} 下载失败")

        # 添加延时避免请求过于频繁
        time.sleep(0.1)

    # 注销 baostock 登录
    bs.logout()
    print(
        f"数据下载完成，共处理 {len(stock_codes)} 只股票，数据保存在 {output_dir} 目录"
    )


# 生成 qlib bin 格式数据
def generate_qlib_bin_data(csv_dir, qlib_dir):
    """
    将 CSV 格式数据转换为 qlib bin 格式

    参数:
        csv_dir: CSV 数据目录
        qlib_dir: qlib bin 数据输出目录
    """
    import subprocess
    import sys

    # 构建 dump_bin.py 命令
    cmd = [
        sys.executable,
        "scripts/dump_bin.py",
        "dump_update",
        # sys.executable, "scripts/dump_bin.py", "dump_fix",
        # sys.executable, "scripts/dump_bin.py", "dump_all",
        "--csv_path",
        csv_dir,
        "--qlib_dir",
        qlib_dir,
        "--include_fields",
        "open,close,high,low,volume,factor",
        "--exclude_fields",
        "date,symbol",
    ]

    print(f"执行命令: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("qlib bin 数据生成成功！")
            print("输出目录:", qlib_dir)
        else:
            print("qlib bin 数据生成失败！")
            print("错误信息:", result.stderr)
    except Exception as e:
        print(f"执行命令时出错: {e}")


def check_latest_date_in_csv(csv_dir):
    """
    检查 CSV 目录下最新文件的日期
    返回: 最新文件的日期，格式为 'YYYY-MM-DD'
    """
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith(".csv")]
    if not csv_files:
        return None
    for file in csv_files:
        stock_info = pd.read_csv(os.path.join(csv_dir, file))
        if not stock_info.empty:
            return stock_info["date"].max()
    return None


if __name__ == "__main__":
    # os.system("export PYTHONPATH=.")
    # 获得当天的日期，格式为 'YYYY-MM-DD'
    today = datetime.date.today().strftime("%Y-%m-%d")

    # 设置输出目录
    csv_output_dir = "qlib_csv_data"
    qlib_output_dir = "~/.qlib/qlib_data/cn_data"

    start_time = check_latest_date_in_csv(csv_output_dir)
    if start_time is None:
        start_time = "2025-07-30"

    print("开始下载股票数据...")
    print(f"时间范围: {start_time} 到 {today}")
    print(f"CSV 输出目录: {csv_output_dir}")
    print(f"Qlib bin 输出目录: {qlib_output_dir}")

    # 第一步：下载数据并保存为 CSV 格式
    download_all_stocks_qlib_format(start_time, today, csv_output_dir)

    # 第二步：转换为 qlib bin 格式
    print("\n开始转换为 qlib bin 格式...")
    generate_qlib_bin_data(csv_output_dir, qlib_output_dir)

    print("\n数据获取和转换完成！")
    print("使用方法:")
    print("1. 在 Python 中初始化 qlib:")
    print("   from qlib.constant import REG_CN")
    print("   qlib.init(provider_uri='~/.qlib/qlib_data/cn_data', region=REG_CN)")
    print("2. 使用 qlib 数据:")
    print("   from qlib.data import D")
    print("   data = D.features(['SH600000'], ['$close', '$volume'])")
