from pprint import pprint

import qlib
import pandas as pd
from qlib.utils.time import Freq
from qlib.utils import flatten_dict
from qlib.contrib.evaluate import backtest_daily
from qlib.contrib.evaluate import risk_analysis
from qlib.contrib.strategy import TopkDropoutStrategy
from qlib.data import D

import pandas as pd
import numpy as np
from qlib.data import D
from qlib.contrib.model.gbdt import LGBModel

qlib.init(provider_uri='~/.qlib/qlib_data/cn_data')


def generate_pred_signal():
    # 1. 准备特征数据（示例：使用 QLib 内置数据接口获取）
    instruments = D.instruments(market='csi300')  # 获取股票池
    start_date = '2020-01-01'
    end_date = '2023-12-31'
    
    # 2. 构建特征矩阵（实际应用中需替换为真实特征工程代码）
    # 这里简化为随机生成特征（实际需用 Alpha158 等特征集）
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # 工作日
    features = pd.DataFrame(
        np.random.randn(len(dates)*len(instruments), 10),  # 10个随机特征
        index=pd.MultiIndex.from_product([dates, instruments], names=['datetime', 'instrument']),
        columns=[f'feature_{i}' for i in range(10)]
    )
    
    # 3. 训练模型（以 LightGBM 为例，与配置文件中的 LGBModel 对应）
    model = LGBModel(
        loss='mse',
        learning_rate=0.2,
        max_depth=8,
        num_leaves=210
    )
    model.fit(features, np.random.randn(len(features)))  # 这里用随机标签模拟训练
    
    # 4. 生成预测分数（即 <PRED> 的核心内容）
    pred_score = model.predict(features)
    
    # 5. 整理为 QLib 策略要求的格式
    pred_df = pd.DataFrame(
        pred_score, 
        index=features.index,  # 继承 [datetime, instrument] 索引
        columns=['score']  # 固定列名 'score'
    )
    
    return pred_df

pred_score = generate_pred_signal()

CSI300_BENCH = "SH000300"
STRATEGY_CONFIG = {
    "topk": 50,
    "n_drop": 5,
    # pred_score, pd.Series
    "signal": pred_score,
}


strategy_obj = TopkDropoutStrategy(**STRATEGY_CONFIG)
report_normal, positions_normal = backtest_daily(
    start_time="2017-01-01", end_time="2020-08-01", strategy=strategy_obj
)
analysis = dict()
# default frequency will be daily (i.e. "day")
analysis["excess_return_without_cost"] = risk_analysis(report_normal["return"] - report_normal["bench"])
analysis["excess_return_with_cost"] = risk_analysis(report_normal["return"] - report_normal["bench"] - report_normal["cost"])

analysis_df = pd.concat(analysis)  # type: pd.DataFrame
pprint(analysis_df)