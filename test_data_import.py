#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试qlib数据导入是否成功
"""

import qlib
from qlib.data import D
from qlib.utils import init_instance_by_config
from qlib.workflow import R
from qlib.workflow.record_temp import SignalRecord, PortAnaRecord
from qlib.contrib.evaluate import backtest_daily
from qlib.contrib.strategy import TopkDropoutStrategy

def test_data_import():
    """测试数据导入是否成功"""
    print("开始测试qlib数据导入...")
    
    # 初始化qlib
    qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region=qlib.constant.REG_CN)
    
    # 测试获取日历数据
    print("测试获取日历数据...")
    try:
        calendar = D.calendar(start_time="1920-01-01", end_time="2026-01-10")
        print(f"成功获取日历数据，共{len(calendar)}个交易日")
        print(f"日历范围: {calendar[0]} 到 {calendar[-1]}")
    except Exception as e:
        print(f"获取日历数据失败: {e}")
        return False
    
    # 测试获取股票列表
    print("\n测试获取股票列表...")
    try:
        # 使用 D.instruments() 创建正确的配置字典
        instruments_config = D.instruments("csi300")
        instruments = D.list_instruments(instruments_config, start_time="1920-01-01", end_time="2026-01-10")
        if isinstance(instruments, dict):
            # 如果是字典格式，获取股票代码列表
            stock_list = list(instruments.keys())
        else:
            # 如果是其他格式，直接转换
            stock_list = list(instruments)
        print(f"成功获取股票列表，共{len(stock_list)}只股票")
        print(f"前5只股票: {stock_list[:5]}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"获取股票列表失败: {e}")
        return False
    
    # 测试获取特征数据
    print("\n测试获取特征数据...")
    try:
        # 获取第一只股票的数据
        if isinstance(instruments, dict):
            first_stock = list(instruments.keys())[0]
        else:
            first_stock = list(instruments)[0]
        fields = ["$close", "$volume", "$factor"]
        data = D.features([first_stock], fields, start_time="2020-01-01", end_time="2020-01-10")
        print(f"成功获取股票 {first_stock} 的特征数据")
        print(f"数据形状: {data.shape}")
        print(f"数据列: {list(data.columns)}")
        print(f"前3行数据:\n{data.head(3)}")
    except Exception as e:
        print(f"获取特征数据失败: {e}")
        return False
    
    # # 测试简单的回测
    # print("\n测试简单回测...")
    # try:
    #     # 配置策略
    #     strategy_config = {
    #         "topk": 50,
    #         "n_drop": 5,
    #     }
        
    #     # 配置回测
    #     backtest_config = {
    #         "start_time": "2020-01-01",
    #         "end_time": "2020-01-31",
    #         "account": 100000000,
    #         "benchmark": "SH000300",
    #         "exchange": "SHSE",
    #     }
        
    #     # 执行回测
    #     strategy_obj = TopkDropoutStrategy(**strategy_config)
    #     sr = SignalRecord(model=strategy_obj, dataset="csi300")
    #     sr.generate()
        
    #     par = PortAnaRecord(signal=sr, strategy=strategy_obj, **backtest_config)
    #     par.generate()
        
    #     print("回测执行成功！")
    #     print(f"回测结果: {par.recorder.read()}")
        
    # except Exception as e:
    #     print(f"回测失败: {e}")
    #     return False
    
    print("\n✅ 所有测试通过！qlib数据导入成功！")
    return True

if __name__ == "__main__":
    success = test_data_import()
    if success:
        print("\n🎉 恭喜！qlib数据已经成功导入并可以正常使用。")
        print("\n您现在可以：")
        print("1. 使用 qlib 进行量化研究")
        print("2. 运行 examples/benchmarks 中的示例")
        print("3. 开始您的量化投资策略开发")
    else:
        print("\n❌ 数据导入测试失败，请检查数据文件。") 