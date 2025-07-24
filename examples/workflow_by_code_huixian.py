#  Copyright (c) Microsoft Corporation.
#  Licensed under the MIT License.
"""
Qlib provides two kinds of interfaces.
(1) Users could define the Quant research workflow by a simple configuration.
(2) Qlib is designed in a modularized way and supports creating research workflow by code just like building blocks.

The interface of (1) is `qrun XXX.yaml`.  The interface of (2) is script like this, which nearly does the same thing as `qrun XXX.yaml`
"""
import qlib
from qlib.constant import REG_CN
from qlib.utils import init_instance_by_config, flatten_dict
from qlib.workflow import R
from qlib.workflow.record_temp import SignalRecord, PortAnaRecord, SigAnaRecord
from qlib.tests.data import GetData
from qlib.tests.config import CSI300_BENCH, CSI300_GBDT_TASK
from qlib.data.dataset import DatasetH
from qlib.data.dataset.handler import DataHandlerLP
from qlib.data import D

# 训练模型
if __name__ == "__main__":
    # use default data
    # 1.数据初始化并获取日历数据
    provider_uri = "~/.qlib/qlib_data/cn_data"  # target_dir
    # GetData().qlib_data(target_dir=provider_uri, region=REG_CN, exists_skip=True)
    qlib.init(provider_uri=provider_uri, region=REG_CN)

    tradedate = D.calendar(start_time='2008-01-01',end_time='2025-6-20',freq='day')
    print(tradedate[:5])

    # 2.获取所有证券代码
    instruments = D.instruments(market='all')
    stock_list = D.list_instruments(
        instruments=instruments,
        # start_time='2008-01-01',
        # end_time='2025-06-20',
        as_list=True)

    print(f"所有股票数量: {len(stock_list)}")


    from qlib.data.filter import NameDFilter, ExpressionDFilter
    #静态Filter:北交所A股
    nameDFilter = NameDFilter(name_rule_re='BJ[0-9!]')
    # 动态Filter:后复权价格大于等于1元
    expressionDFilter = ExpressionDFilter(rule_expression = '$close>=1')
    #按以上两个过滤条件获取新的股票代码集
    instruments = D.instruments(market='all')
    stock_list = D.list_instruments(
        instruments=instruments,
        start_time='2008-01-01',
        end_time='2025-06-20',
        as_list=True)
    # 展示条件过滤后的5个股票代码
    print("条件过滤后的5个股票代码：")
    print(stock_list[-5:])

    #3.获取指定股票指定日期指定字段数据
    # features_df = D.features(instruments=['SZ300891'],
    #  fields=['$close',' $volume'],
    #  start_time='2020-01-01',
    #  end_time='2020-11-30',
    #  freq='day')
    # print(features_df.head())

    data_handler_config = {

        # 完整数据起止日期
        "start_time": "2008-01-01",
        "end_time": "2025-06-20",

        # 拟合数据起止日期，为完整数据起止日期数据的子集
        "fit_start_time": "2008-01-01",
        "fit_end_time": "2018-12-31",

        # 股票池
        # "instruments": instruments,
        "instruments": "csi300" , # 沪深300
        # "instruments": "csi500" , # 中证500
        # "instruments": "csi1000" , # 中证1000
        # "instruments": "csi3000" , # 中证3000
        # "instruments": "csi5000" , # 中证5000
        # "instruments": "csi10000" , # 中证10000
        # "instruments": "csi100000" , # 中证100000
        # "instruments": "sz500" , # 上证500
        # "instruments": "sz1000" , # 上证1000
        # "instruments": "sz1500" , # 上证1500
        # "instruments": "sz2000" , # 上证2000
        # "instruments": "sz2500" , # 上证2500
        # "instruments": "sz3000" , # 上证3000
        # "instruments": "sz3500" , # 上证3500
    }

    print(f"data_handler_config: {data_handler_config}")

    task = {
        "model": {
            "class": "LGBModel", # 模型名称
            "module_path": "qlib.contrib.model.gbdt", #AI模型所在路径
            "kwargs": {
                # #LGBmodel的超参，调参数
                "loss": "mse", # 损失函数，此处设置为均方误差
                "colsample_bytree": 0.8879, # 列采样比列
                "learning_rate": 0.0421, # 学习率
                "subsample": 0.8789, # 行采样比例
                "lambda_l1": 205.6999, # L1正则
                "lambda_l2": 580.9768, # L2正则
                "max_depth": 8, # 最大树深度
                "num_leaves": 210, # 最大叶子节点数
                "num_threads": 20, # 最大并行线程数

                # 新增加的参数
                "verbose": 1, # 显示训练过程
                "min_data_in_leaf": 10, # 最小叶子节点样本数
                "min_child_samples": 100,  # 最小子节点样本数
                "num_boost_round": 2000,  # 最大轮数
            },
        },

        # （数据集）-参数及说明
        "dataset": {
            "class": "DatasetH", # 数据集名称
            "module_path": "qlib.data.dataset", # 数据集所在路径

            # DatasetH模型参数
            "kwargs": {
                # 因子库参数
                "handler": {
                    # Alpha158和Alpha360两类量价因子库，可根据需要自定义因子库
                    "class": "Alpha158", # 因子库名称，此处使用qlib自带的Alpha158
                    "module_path": "qlib.contrib.data.handler", # 因子库所在路径
                    "kwargs": data_handler_config, # Alpha158的参数
                },
                # 数据集划分参数
                "segments": {
                    "train": ("2008-01-01", "2018-12-31"), # 训练集
                    "valid": ("2019-01-01", "2020-12-31"), # 验证集
                    "test": ("2021-01-01", "2025-06-20"), # 测试集
                },
            },
        },
    }

    # 4.初始化模型和数据集
    print(f"task: {task}")
    model = init_instance_by_config(task["model"])

    print(f"model: {model}")
    dataset = init_instance_by_config(task["dataset"])

    print(f"dataset: {dataset}")

    # NOTE: This line is optional # 可选的，说明数据集可以独立使用
    # It demonstrates that the dataset can be used standalone. # 说明数据集可以独立使用
    # 5.准备数据
    df = dataset.prepare("train")
    print(df.head())

    # 模型预测，回测
    port_analysis_config = {
        "executor": {
            "class": "SimulatorExecutor",
            "module_path": "qlib.backtest.executor",
            "kwargs": {
                "time_per_step": "day",
                "generate_portfolio_metrics": True,
            },
        },

        # 交易策略
        "strategy": {
            "class": "TopkDropoutStrategy", 
            # "class": "MovingAverageStrategy",
            "module_path": "qlib.contrib.strategy.signal_strategy",
            "kwargs": {
                "signal": (model, dataset),
                "topk": 50, # 50个股票
                "n_drop": 5, # 5个股票  
            },
            # TopkDropoutStrategy:每日等权持有topk=50只股票，
            # 同时每日卖出持仓股票中最新预测收益最低的n_drop=5只股票
            # 买入未持仓股票中最新预测收益最高的n_drop=5只股票。
        },

        # 回测参数
        "backtest": {
            "start_time": "2021-01-01", # 测试开始时间
            "end_time": "2025-6-20", # 测试结束时间
            "account": 100000, # 账户启动资金
            "benchmark": CSI300_BENCH, # 业绩比较基准指数
            # 交易成本参数
            "exchange_kwargs": {
                "freq": "day", # 交易频率
                "limit_threshold": 0.095, # 涨跌停限制
                "deal_price": "close", # 成交价格，按照收盘价格
                "open_cost": 0.0001, # 开仓交易费率，万1佣金
                "close_cost": 0.0006, # 平仓交易费率，万5印花税+万1佣金
                "min_cost": 1, # 最低交易费用1元
            },
        },
    }
    
    # start exp to trained model # 开始实验，训练模型
    with R.start(experiment_name="train_model"):
        R.log_params(**flatten_dict(task))
        # 拟合模型
        model.fit(dataset)
        R.save_objects(**{"params.pkl": model})

        # 预测模型
        recorder = R.get_recorder()
        rid = R.get_recorder().id


    # 运行回测
    with R.start(experiment_name="crypto_backtest"):
        # 加载训练好的模型
        recorder = R.get_recorder(recorder_id=rid, experiment_name="train_model")
        model = recorder.load_object("params.pkl")

        # 创建回测recorder
        recorder = R.get_recorder()
        ba_rid = recorder.id

        # 生成预测信号
        print("生成预测信号...")
        sr = SignalRecord(model, dataset, recorder)
        sr.generate()

        sar = SigAnaRecord(recorder)
        sar.generate()

        # 执行回测
        print("执行回测...")
        # backtest. If users want to use backtest based on their own prediction,
        # please refer to https://qlib.readthedocs.io/en/latest/component/recorder.html#record-template.
        par = PortAnaRecord(recorder, port_analysis_config, "day")
        par.generate()
        
        print(f"回测完成! Recorder ID: {ba_rid}")
        print("done")