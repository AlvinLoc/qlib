# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
import numpy as np
import pandas as pd
from multiprocessing import Pool, cpu_count, Manager
from functools import partial
import warnings
import gc
import time
from datetime import datetime
warnings.filterwarnings('ignore')

from qlib.data import D
from qlib.model.riskmodel import StructuredCovEstimator


def process_single_date_optimized(args):
    """
    优化的单日期处理函数
    
    Parameters
    ----------
    args : tuple
        (date, ref_date, codes, price_data, riskdata_root, process_id)
    
    Returns
    -------
    dict
        处理结果信息
    """
    date, ref_date, codes, price_data, riskdata_root, process_id = args
    
    start_time = time.time()
    
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
        pd.Series(np.sqrt(var_u), index=codes).to_pickle(root + "/specific_risk.pkl")
        
        # 清理内存
        del ret, F, cov_b, var_u, riskmodel
        gc.collect()
        
        processing_time = time.time() - start_time
        
        return {
            'success': True,
            'date': date,
            'process_id': process_id,
            'processing_time': processing_time,
            'error': None
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        return {
            'success': False,
            'date': date,
            'process_id': process_id,
            'processing_time': processing_time,
            'error': str(e)
        }


def prepare_data_mp_optimized(riskdata_root="./riskdata", T=240, start_time="2016-01-01", 
                             n_processes=None, chunk_size=50, memory_limit_gb=8):
    """
    优化的多进程版本，包含内存管理和性能监控
    
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
    memory_limit_gb : float
        内存限制（GB）
    """
    # 设置进程数
    if n_processes is None:
        n_processes = min(cpu_count(), 8)
    
    print(f"=== 优化的多进程风险数据准备 ===")
    print(f"进程数: {n_processes}")
    print(f"块大小: {chunk_size}")
    print(f"内存限制: {memory_limit_gb}GB")
    print(f"开始时间: {datetime.now()}")
    
    # 加载数据
    print("加载数据...")
    load_start = time.time()
    
    universe = D.features(D.instruments("csi300"), ["$close"], start_time=start_time).swaplevel().sort_index()
    price_all = (
        D.features(D.instruments("all"), ["$close"], start_time=start_time).squeeze().unstack(level="instrument")
    )
    
    load_time = time.time() - load_start
    print(f"数据加载完成，耗时: {load_time:.2f}秒")
    
    # 准备任务参数
    print("准备任务参数...")
    tasks = []
    for i in range(T - 1, len(price_all)):
        date = price_all.index[i]
        ref_date = price_all.index[i - T + 1]
        
        codes = universe.loc[date].index
        price = price_all.loc[ref_date:date, codes]
        
        tasks.append((date, ref_date, codes, price, riskdata_root, i % n_processes))
    
    print(f"总共需要处理 {len(tasks)} 个日期")
    
    # 分块处理
    successful = 0
    failed = 0
    total_processing_time = 0
    
    with Pool(processes=n_processes) as pool:
        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i:i+chunk_size]
            chunk_num = i//chunk_size + 1
            total_chunks = (len(tasks)-1)//chunk_size + 1
            
            print(f"\n处理块 {chunk_num}/{total_chunks} ({len(chunk)} 个日期)")
            chunk_start = time.time()
            
            # 使用imap_unordered提高效率
            results = list(pool.imap_unordered(process_single_date_optimized, chunk))
            
            # 统计结果
            chunk_successful = sum(1 for r in results if r['success'])
            chunk_failed = len(results) - chunk_successful
            chunk_time = time.time() - chunk_start
            
            successful += chunk_successful
            failed += chunk_failed
            total_processing_time += chunk_time
            
            # 打印块处理结果
            print(f"块 {chunk_num} 完成:")
            print(f"  成功: {chunk_successful}, 失败: {chunk_failed}")
            print(f"  耗时: {chunk_time:.2f}秒")
            print(f"  平均每日期: {chunk_time/len(chunk):.2f}秒")
            
            # 打印错误信息
            if chunk_failed > 0:
                print("  错误详情:")
                for result in results:
                    if not result['success']:
                        print(f"    {result['date']}: {result['error']}")
            
            # 内存清理
            del results
            gc.collect()
    
    # 最终统计
    total_time = time.time() - load_start
    print(f"\n=== 处理完成 ===")
    print(f"总耗时: {total_time:.2f}秒")
    print(f"数据加载: {load_time:.2f}秒 ({load_time/total_time*100:.1f}%)")
    print(f"数据处理: {total_processing_time:.2f}秒 ({total_processing_time/total_time*100:.1f}%)")
    print(f"成功: {successful}")
    print(f"失败: {failed}")
    print(f"成功率: {successful/(successful+failed)*100:.2f}%")
    print(f"平均每日期处理时间: {total_processing_time/(successful+failed):.2f}秒")


def prepare_data_mp_with_monitoring(riskdata_root="./riskdata", T=240, start_time="2016-01-01", 
                                   n_processes=None, monitor_interval=10):
    """
    带监控的多进程版本
    
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
    monitor_interval : int
        监控间隔（秒）
    """
    import psutil
    from threading import Thread
    import time
    
    # 设置进程数
    if n_processes is None:
        n_processes = min(cpu_count(), 8)
    
    print(f"=== 带监控的多进程版本 ===")
    print(f"进程数: {n_processes}")
    print(f"监控间隔: {monitor_interval}秒")
    
    # 创建共享计数器
    manager = Manager()
    counter = manager.Value('i', 0)
    successful_counter = manager.Value('i', 0)
    failed_counter = manager.Value('i', 0)
    
    def monitor_resources():
        """监控系统资源使用情况"""
        process = psutil.Process()
        while True:
            try:
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                print(f"[监控] CPU: {cpu_percent:.1f}%, 内存: {memory_mb:.1f}MB, "
                      f"已处理: {counter.value}, 成功: {successful_counter.value}, 失败: {failed_counter.value}")
                
                time.sleep(monitor_interval)
            except KeyboardInterrupt:
                break
    
    # 启动监控线程
    monitor_thread = Thread(target=monitor_resources, daemon=True)
    monitor_thread.start()
    
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
        
        tasks.append((date, ref_date, codes, price, riskdata_root, i % n_processes))
    
    print(f"总共需要处理 {len(tasks)} 个日期")
    
    # 处理函数（带计数器更新）
    def process_with_counter(args):
        result = process_single_date_optimized(args)
        counter.value += 1
        if result['success']:
            successful_counter.value += 1
        else:
            failed_counter.value += 1
        return result
    
    # 使用多进程处理
    with Pool(processes=n_processes) as pool:
        results = list(pool.imap_unordered(process_with_counter, tasks))
    
    # 最终统计
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"\n=== 处理完成 ===")
    print(f"成功: {successful}")
    print(f"失败: {failed}")
    print(f"成功率: {successful/(successful+failed)*100:.2f}%")


if __name__ == "__main__":
    import qlib

    qlib.init(provider_uri="~/.qlib/qlib_data/cn_data")

    # 选择不同的优化版本
    print("=== 优化版本1: 基础优化版本 ===")
    prepare_data_mp_optimized()
    
    # print("=== 优化版本2: 带监控版本 ===")
    # prepare_data_mp_with_monitoring() 