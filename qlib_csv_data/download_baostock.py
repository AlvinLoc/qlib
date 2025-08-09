import asyncio
import baostock as bs
import pandas as pd
import os
import time
import datetime
import re
from tqdm import tqdm
from loguru import logger
from multiprocessing import Pool

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


def filter_stock_codes(stock_codes):
    """
    筛选股票代码，删除科创板、创业板、北交所和ST股票
    
    参数:
        stock_codes (list): 原始股票代码列表
        
    返回:
        list: 筛选后的股票代码列表
        
    筛选规则:
        1. 排除科创板股票（688开头）
        2. 排除创业板股票（300、301开头）
        3. 排除北交所股票（8开头）
        4. 排除ST股票（需要查询股票名称）
    """
    filtered_codes = []
    excluded_count = 0
    
    print("开始筛选股票...")
    
    # for code in stock_codes:
    #     # 提取股票代码的数字部分
    #     if "." in code:
    #         stock_number = code.split(".")[1]
    #     else:
    #         stock_number = code
        
    #     # 排除科创板（688开头）
    #     if stock_number.startswith("688"):
    #         excluded_count += 1
    #         continue
            
    #     # 排除创业板（300、301开头）
    #     if stock_number.startswith("300") or stock_number.startswith("301"):
    #         excluded_count += 1
    #         continue
            
    #     # 排除北交所（8开头）
    #     if stock_number.startswith("8"):
    #         excluded_count += 1
    #         continue
        
    #     # 保留符合条件的股票
    #     filtered_codes.append(code)
    
    # print(f"原始股票数量: {len(stock_codes)}")
    # print(f"筛选后股票数量: {len(filtered_codes)}")
    # print(f"排除股票数量: {excluded_count}")
    # print(f"排除详情:")
    # print(f"  - 科创板(688开头): 约 {len([c for c in stock_codes if c.split('.')[1].startswith('688')])} 只")
    # print(f"  - 创业板(300/301开头): 约 {len([c for c in stock_codes if c.split('.')[1].startswith(('300', '301'))])} 只")
    # print(f"  - 北交所(8开头): 约 {len([c for c in stock_codes if c.split('.')[1].startswith('8')])} 只")
    
    return stock_codes


# 获取所有股票代码
def get_all_stock_codes(valid_date=None):
    if not login_baostock():
        return []
    """
    获取当前交易日所有可交易的股票代码列表
    返回: 股票代码列表，格式如 ['sh.600000', 'sz.000001', ...]
    """
    if valid_date is None:
        valid_date = datetime.date.today().strftime("%Y-%m-%d")
    rs = bs.query_all_stock(day=valid_date)
    if rs.error_code != "0":
        print(f"获取股票列表失败，错误代码: {rs.error_code}，错误信息: {rs.error_msg}")
        return []
    data_list = []
    while (rs.error_code == "0") & rs.next():
        data_list.append(rs.get_row_data())
    df = pd.DataFrame(data_list, columns=rs.fields)
    # 只保留交易状态为 '1'（正常交易）的股票
    stock_codes = df[df["tradeStatus"] == "1"]["code"].tolist()
    filtered_stock_codes = []
    for code in stock_codes:
        qlib_stock_code = code.upper().replace(".", "")
        name_rule_re='^(?!BJ[0-9]+)(?!SZ30[0-9]+)(?!SH688[0-9]+).*$'
        if not re.match(name_rule_re, qlib_stock_code):
            continue
        filtered_stock_codes.append(code)
    if DEBUG_MODE:
        filtered_stock_codes = filtered_stock_codes[:10]
    return filtered_stock_codes


# 下载单只股票数据
def download_stock_data(stock_code, start_date, end_date):
    """
    下载指定股票在指定时间范围内的历史K线数据

    参数:
        stock_code: 股票代码，如 'sh.600000'
        start_date: 开始日期，格式 'YYYY-MM-DD'
        end_date: 结束日期，格式 'YYYY-MM-DD'

    返回: DataFrame 包含股票历史数据，失败时返回 None

    数据字段:
        date: 交易日期
        code: 股票代码
        open: 开盘价
        high: 最高价
        low: 最低价
        close: 收盘价
        preclose: 前收盘价
        volume: 成交量
        amount: 成交额
        adjustflag: 复权类型
        turn: 换手率
        tradestatus: 交易状态
        pctChg: 涨跌幅
        isST: 是否ST股票

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
            "date": pd.to_datetime(df["date"])[:10],
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
def download_all_stocks_qlib_format(start_date, end_date, output_dir="qlib_csv_data", supplement_days=2):
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
        qlib_stock_code = stock_code.upper().replace(".", "")
        name_rule_re='^(?!BJ[0-9]+)(?!SZ30[0-9]+)(?!SH688[0-9]+).*$'
        if not re.match(name_rule_re, qlib_stock_code):
            print(f"股票 {qlib_stock_code} 不符合条件，跳过")
            continue

        print(f"正在处理第 {i + 1}/{len(stock_codes)} 只股票: {stock_code}")

        # 下载股票数据
        df = download_stock_data(stock_code, start_date, end_date)

        if df is not None and not df.empty:
            # 转换为 qlib 格式
            qlib_df = convert_to_qlib_format(df, stock_code)

            if qlib_df is not None and not qlib_df.empty:
                # 保存为 CSV 文件，文件名为股票代码
                csv_filename = f"{qlib_stock_code}.csv"
                csv_path = os.path.join(output_dir, csv_filename)

                # 补充两天空行
                csv_stock_code = df.iloc[0, 0]
                for i in range(supplement_days):
                    day = datetime.datetime.strptime(
                        end_date, "%Y-%m-%d"
                    ) + datetime.timedelta(days=(i + 1))
                    date_str = day.strftime("%Y-%m-%d")
                    row = [csv_stock_code, date_str] + [None] * (qlib_df.shape[1] - 2)
                    qlib_df = pd.concat([qlib_df, pd.DataFrame([row], columns=qlib_df.columns)], ignore_index=True)

                # 检查文件是否存在
                if os.path.exists(csv_path):
                    print(f"文件 {csv_path} 已存在，追加数据")
                    existed_df = pd.read_csv(csv_path)
                    qlib_df = pd.concat([existed_df, qlib_df], ignore_index=True)

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
    
    # 构建 dump_bin.py 命令 - 使用 dump_all 模式而不是 dump_update
    cmd = [
        sys.executable, "scripts/dump_bin.py", "dump_all",
        # sys.executable, "scripts/dump_bin.py", "dump_fix",
        # sys.executable, "scripts/dump_bin.py", "dump_update",
        "--csv_path", csv_dir,
        "--qlib_dir", qlib_dir,
        "--include_fields", "open,close,high,low,volume,factor",
        "--exclude_fields", "date,symbol"
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


# def check_latest_date_in_csv(csv_dir):
#     """
#     检查 CSV 目录下最新文件的日期
#     返回: 最新文件的日期，格式为 'YYYY-MM-DD'
#     """
#     csv_files = [f for f in os.listdir(csv_dir) if f.endswith(".csv")]
#     if not csv_files:
#         return None
#     for file in csv_files:
#         stock_info = pd.read_csv(os.path.join(csv_dir, file))
#         if not stock_info.empty:
#             return stock_info["date"].max()
#     return None


def main_old():
    # os.system("export PYTHONPATH=.")

    # 获得当天的日期，格式为 'YYYY-MM-DD'
    today = datetime.date.today().strftime("%Y-%m-%d")

    # 设置输出目录
    csv_output_dir = "qlib_csv_data"
    qlib_output_dir = "~/.qlib/qlib_data/cn_data"

    # start_time = check_latest_date_in_csv(csv_output_dir)
    # if start_time is None:
    start_time = "2022-01-01"

    print("开始下载股票数据...")
    print(f"时间范围: {start_time} 到 {today}")
    print(f"CSV 输出目录: {csv_output_dir}")
    print(f"Qlib bin 输出目录: {qlib_output_dir}")

    # 第一步：下载数据并保存为 CSV 格式（不下载数据注释掉）
    download_all_stocks_qlib_format(start_time, today, csv_output_dir)

    # 第二步：转换为 qlib bin 格式
    print("\n开始转换为 qlib bin 格式...")
    # generate_qlib_bin_data(csv_output_dir, qlib_output_dir)

    print("\n数据获取和转换完成！")
    print("使用方法:")
    print("1. 在 Python 中初始化 qlib:")
    print("   from qlib.constant import REG_CN")
    print("   qlib.init(provider_uri='~/.qlib/qlib_data/cn_data', region=REG_CN)")
    print("2. 使用 qlib 数据:")
    print("   from qlib.data import D")
    print("   data = D.features(['SH600000'], ['$close', '$volume'])")

def get_latest_valid_data_date_from_csv(df):
    """
    获取 CSV 文件中最新有效数据日期
    """
    # 获取high列不为空的最后一行
    last_valid_row = df[df["high"].notna()].iloc[-1]
    date_str = str(last_valid_row["date"])
    return date_str[:10]

def get_latest_valid_data_date_from_dir(csv_dir):
    """
    获取 CSV 目录下最新文件的日期
    返回: 最新文件的日期，格式为 'YYYY-MM-DD'
    """
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith(".csv")]
    assert len(csv_files) > 0, "CSV 目录下没有文件"

    csv_file = csv_files[0]
    df = pd.read_csv(os.path.join(csv_dir, csv_file))
    return get_latest_valid_data_date_from_csv(df)

def get_next_trade_date(current_date_str, offset_days=1):
    """
    获取下一个交易日
    """
    print(f"current_date_str: {current_date_str}, offset_days: {offset_days}")
    current_date = datetime.datetime.strptime(current_date_str, "%Y-%m-%d")
    for i in range(offset_days):
        # 如果是星期五，则加3天
        if current_date.weekday() == 4:
            current_date += datetime.timedelta(days=3)
        else:
            current_date += datetime.timedelta(days=1)
    return current_date.strftime("%Y-%m-%d")

def stick_one_stock_data(args):
    stock_code, latest_valid_data_date, end_date, csv_dir, extend_days = args
    df = download_stock_data(stock_code, latest_valid_data_date, end_date)
    if df is not None and not df.empty:
        qlib_df = convert_to_qlib_format(df, stock_code)
        if qlib_df is None or qlib_df.empty:
            return

        qlib_stock_code = stock_code.upper().replace(".", "")
        csv_file = f"{qlib_stock_code}.csv"
        csv_path = os.path.join(csv_dir, csv_file)
        assert os.path.exists(csv_path), f"文件 {csv_path} 不存在"
        existed_df = pd.read_csv(csv_path)
        existed_df = existed_df[existed_df["date"] <= latest_valid_data_date]
        qlib_df = pd.concat([existed_df, qlib_df], ignore_index=True)
        new_latest_valid_data_date = get_latest_valid_data_date_from_csv(qlib_df)
        for i in range(extend_days):
            trade_date = get_next_trade_date(new_latest_valid_data_date, i+1)
            date_str = trade_date
            row = [qlib_stock_code, date_str] + [None] * (qlib_df.shape[1] - 2)
            qlib_df = pd.concat([qlib_df, pd.DataFrame([row], columns=qlib_df.columns)], ignore_index=True)
        # 将所有的date列变成str，并只保留[:10]
        qlib_df["date"] = qlib_df["date"].astype(str).str[:10]
        qlib_df.to_csv(csv_path, index=False)
        logger.critical(f"股票 {stock_code} 拼接完成")
    else:
        logger.error(f"股票 {stock_code} 下载失败")
    time.sleep(0.1)

def stitch_stock_data(stock_codes, latest_valid_data_date, csv_dir, end_date=None, workers=1, extend_days=2):
    """
    拼接股票数据
    """
    if not login_baostock():
        return

    if end_date is None:
        end_date = datetime.date.today().strftime("%Y-%m-%d")

    tasks = [(code, latest_valid_data_date, end_date, csv_dir, extend_days) for code in stock_codes]

    logger.critical(f"开始拼接股票数据，共 {len(tasks)} 只股票")
    if workers > 1:
        with Pool(workers) as p:
            p.imap_unordered(
                stick_one_stock_data, tasks
            )
    else:
        for arg in tqdm(tasks, desc="拼接股票数据"):
            stick_one_stock_data(arg)

import threading

def wait_for_user_confirm(timeout_minutes=30):
    """
    等待用户输入Y，如果输入Y直接返回True，输入其他返回False，30min不输入直接返回True
    """
    result = {"value": None}

    def ask_input():
        user_input = input("请确认是否继续（输入Y确认，其他任意键取消，30分钟不输入自动确认）: ").strip()
        if user_input.upper() == "Y":
            result["value"] = True
        else:
            result["value"] = False

    input_thread = threading.Thread(target=ask_input, daemon=True)
    input_thread.start()
    input_thread.join(timeout=timeout_minutes * 60)
    if result["value"] is None:
        print("超时未输入，自动确认。")
        return True
    return result["value"]


def main():
    # 获取所有股票的最后一个有效天
    csv_dir = "qlib_csv_data"
    latest_valid_data_date = get_latest_valid_data_date_from_dir(csv_dir)
    logger.critical(f"最新有效数据日期: {latest_valid_data_date}")

    # 获取所有股票的代码
    stock_codes = get_all_stock_codes(latest_valid_data_date)
    logger.critical(f"共 {len(stock_codes)} 只股票待更新")

    # 拼接股票数据
    stitch_stock_data(stock_codes, latest_valid_data_date, csv_dir)

    # 获取确认信号或者等待10min
    should_convert = wait_for_user_confirm(timeout_minutes=10)

    qlib_output_dir = "~/.qlib/qlib_data/cn_data"
    if should_convert:
        generate_qlib_bin_data(csv_dir, qlib_output_dir)

if __name__ == "__main__":
    main()