# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
import numpy as np
import pandas as pd
from multiprocessing import Pool, cpu_count
from functools import partial
import warnings
warnings.filterwarnings('ignore')

from qlib.data import D
from qlib.model.riskmodel import StructuredCovEstimator


def process_single_date(args):
    """
    处理单个日期的风险数据
    
    Parameters
    ----------
    args : tuple
        (date, ref_date, codes, price_data, riskdata_root)
    
    Returns
    -------
    bool
        处理是否成功
    """
    date, ref_date, codes, price_data, riskdata_root = args
    
    try:
        # 计算收益率并移除极端值
        ret = price_data.pct_change()
        ret.clip(ret.quantile(0.025), ret.quantile(0.975), axis=1, inplace=True)

        # 运行风险模型
        riskmodel = StructuredCovEstimator()
        F, cov_b, var_u = riskmodel.predict(ret, is_price=False, return_decomposed_components=True)

        # 保存风险数据
        root = riskdata_root + "/" + date.strftime("%Y%m%d")
        os.makedirs(root, exist_ok=True)

        pd.DataFrame(F, index=codes).to_pickle(root + "/factor_exp.pkl")
        pd.DataFrame(cov_b).to_pickle(root + "/factor_cov.pkl")
        # for specific_risk we follow the convention to save volatility
        pd.Series(np.sqrt(var_u), index=codes).to_pickle(root + "/specific_risk.pkl")
        
        print(f"成功处理日期: {date}")
        return True
        
    except Exception as e:
        print(f"处理日期 {date} 时出错: {str(e)}")
        return False


def prepare_data_mp(riskdata_root="./riskdata", T=240, start_time="2016-01-01", n_processes=None):
    """
    多进程版本的风险数据准备
    
    Parameters
    ----------
    riskdata_root : str
        风险数据保存路径
    T : int
        时间窗口长度
    start_time : str
        开始时间
    n_processes : int, optional
        进程数，默认为CPU核心数
    """
    # 设置进程数
    if n_processes is None:
        # n_processes = min(cpu_count(), 8)  # 限制最大进程数为8
        n_processes = 32
    
    print(f"使用 {n_processes} 个进程进行并行处理")
    
    # 加载数据
    print("加载数据...")
    universe = D.features(D.instruments("csi300"), ["$close"], start_time=start_time).swaplevel().sort_index()

    price_all = (
        D.features(D.instruments("all"), ["$close"], start_time=start_time).squeeze().unstack(level="instrument")
    )
    
    # 准备任务参数
    tasks = []
    for i in range(T - 1, len(price_all)):
        date = price_all.index[i]
        ref_date = price_all.index[i - T + 1]
        
        codes = universe.loc[date].index
        price = price_all.loc[ref_date:date, codes]
        
        tasks.append((date, ref_date, codes, price, riskdata_root))
    
    print(f"总共需要处理 {len(tasks)} 个日期")
    
    # 使用多进程处理
    with Pool(processes=n_processes) as pool:
        results = pool.map(process_single_date, tasks)
    
    # 统计结果
    successful = sum(results)
    failed = len(results) - successful
    print(f"\n处理完成:")
    print(f"成功: {successful}")
    print(f"失败: {failed}")
    print(f"成功率: {successful/len(results)*100:.2f}%")


def prepare_data_mp_chunked(riskdata_root="./riskdata", T=240, start_time="2016-01-01", 
                           n_processes=None, chunk_size=10):
    """
    分块多进程版本，适合大数据集
    
    Parameters
    ----------
    riskdata_root : str
        风险数据保存路径
    T : int
        时间窗口长度
    start_time : str
        开始时间
    n_processes : int, optional
        进程数，默认为CPU核心数
    chunk_size : int
        每个块的大小
    """
    # 设置进程数
    if n_processes is None:
        n_processes = min(cpu_count(), 8)
    
    print(f"使用 {n_processes} 个进程，块大小 {chunk_size}")
    
    # 加载数据
    print("加载数据...")
    universe = D.features(D.instruments("csi300"), ["$close"], start_time=start_time).swaplevel().sort_index()

    price_all = (
        D.features(D.instruments("all"), ["$close"], start_time=start_time).squeeze().unstack(level="instrument")
    )
    
    # 准备任务参数
    tasks = []
    for i in range(T - 1, len(price_all)):
        date = price_all.index[i]
        ref_date = price_all.index[i - T + 1]
        
        codes = universe.loc[date].index
        price = price_all.loc[ref_date:date, codes]
        
        tasks.append((date, ref_date, codes, price, riskdata_root))
    
    print(f"总共需要处理 {len(tasks)} 个日期")
    
    # 分块处理
    successful = 0
    failed = 0
    
    with Pool(processes=n_processes) as pool:
        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i:i+chunk_size]
            print(f"处理块 {i//chunk_size + 1}/{(len(tasks)-1)//chunk_size + 1} ({len(chunk)} 个日期)")
            
            results = pool.map(process_single_date, chunk)
            
            successful += sum(results)
            failed += len(results) - sum(results)
    
    print(f"\n处理完成:")
    print(f"成功: {successful}")
    print(f"失败: {failed}")
    print(f"成功率: {successful/(successful+failed)*100:.2f}%")


def prepare_data_mp_with_progress(riskdata_root="./riskdata", T=240, start_time="2016-01-01", 
                                 n_processes=None, show_progress=True):
    """
    带进度显示的多进程版本
    
    Parameters
    ----------
    riskdata_root : str
        风险数据保存路径
    T : int
        时间窗口长度
    start_time : str
        开始时间
    n_processes : int, optional
        进程数，默认为CPU核心数
    show_progress : bool
        是否显示进度
    """
    from tqdm import tqdm
    
    # 设置进程数
    if n_processes is None:
        # n_processes = min(cpu_count(), 8)
        n_processes = 32
    
    print(f"使用 {n_processes} 个进程进行并行处理")
    
    # 加载数据
    print("加载数据...")
    universe = D.features(D.instruments("csi300"), ["$close"], start_time=start_time).swaplevel().sort_index()

    price_all = (
        D.features(D.instruments("all"), ["$close"], start_time=start_time).squeeze().unstack(level="instrument")
    )
    
    # 准备任务参数
    tasks = []
    for i in range(T - 1, len(price_all)):
        date = price_all.index[i]
        ref_date = price_all.index[i - T + 1]
        
        codes = universe.loc[date].index
        price = price_all.loc[ref_date:date, codes]
        
        tasks.append((date, ref_date, codes, price, riskdata_root))
    
    print(f"总共需要处理 {len(tasks)} 个日期")
    
    # 使用多进程处理
    successful = 0
    failed = 0
    
    with Pool(processes=n_processes) as pool:
        if show_progress:
            with tqdm(total=len(tasks), desc="处理进度") as pbar:
                for result in pool.imap_unordered(process_single_date, tasks):
                    if result:
                        successful += 1
                    else:
                        failed += 1
                    pbar.update(1)
        else:
            results = pool.map(process_single_date, tasks)
            successful = sum(results)
            failed = len(results) - successful
    
    print(f"\n处理完成:")
    print(f"成功: {successful}")
    print(f"失败: {failed}")
    print(f"成功率: {successful/(successful+failed)*100:.2f}%")


if __name__ == "__main__":
    import qlib

    qlib.init(provider_uri="~/.qlib/qlib_data/cn_data")

    # 选择不同的多进程版本
    # print("=== 多进程版本1: 基础版本 ===")
    # prepare_data_mp()
    
    # print("=== 多进程版本2: 分块版本 ===")
    # prepare_data_mp_chunked()
    
    print("=== 多进程版本3: 带进度显示版本 ===")
    prepare_data_mp_with_progress() 