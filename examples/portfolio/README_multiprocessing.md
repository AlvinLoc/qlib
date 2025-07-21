# 多进程风险数据准备

本目录包含了原始串行版本和多进程优化版本的风险数据准备脚本。

## 文件说明

### 原始版本
- `prepare_riskdata.py` - 原始串行处理版本

### 多进程版本
- `prepare_riskdata_mp.py` - 基础多进程版本
- `prepare_riskdata_mp_optimized.py` - 优化的多进程版本

## 性能对比

| 版本 | 特点 | 适用场景 |
|------|------|----------|
| 原始版本 | 串行处理，简单可靠 | 小数据集，调试阶段 |
| 基础多进程版本 | 并行处理，提高速度 | 中等数据集 |
| 优化多进程版本 | 内存管理，错误处理，监控 | 大数据集，生产环境 |

## 使用方法

### 1. 基础多进程版本

```python
from prepare_riskdata_mp import prepare_data_mp

# 基本使用
prepare_data_mp()

# 自定义参数
prepare_data_mp(
    riskdata_root="./my_riskdata",
    T=240,
    start_time="2018-01-01",
    n_processes=4
)
```

### 2. 优化多进程版本

```python
from prepare_riskdata_mp_optimized import prepare_data_mp_optimized

# 基本使用
prepare_data_mp_optimized()

# 自定义参数
prepare_data_mp_optimized(
    riskdata_root="./my_riskdata",
    T=240,
    start_time="2018-01-01",
    n_processes=6,
    chunk_size=30,
    memory_limit_gb=16
)
```

### 3. 带监控的版本

```python
from prepare_riskdata_mp_optimized import prepare_data_mp_with_monitoring

# 需要安装psutil: pip install psutil
prepare_data_mp_with_monitoring(
    n_processes=8,
    monitor_interval=5  # 每5秒输出一次监控信息
)
```

## 参数说明

### 通用参数
- `riskdata_root`: 风险数据保存路径
- `T`: 时间窗口长度（默认240天）
- `start_time`: 开始时间
- `n_processes`: 进程数（默认CPU核心数，最大8）

### 优化版本特有参数
- `chunk_size`: 每个块的大小（默认50）
- `memory_limit_gb`: 内存限制（GB）
- `monitor_interval`: 监控间隔（秒）

## 性能优化建议

### 1. 进程数设置
```python
# 根据CPU核心数设置
n_processes = min(cpu_count(), 8)  # 限制最大8个进程

# 根据内存情况调整
# 如果内存充足，可以增加进程数
# 如果内存不足，减少进程数或增加chunk_size
```

### 2. 内存管理
```python
# 大数据集建议使用分块处理
chunk_size = 30  # 每块处理30个日期

# 设置内存限制
memory_limit_gb = 8  # 限制内存使用8GB
```

### 3. 错误处理
- 优化版本包含完整的错误处理
- 失败的日期会被记录，不会影响其他日期的处理
- 最终会输出成功率统计

## 监控功能

### 系统资源监控
```python
# 实时监控CPU和内存使用
[监控] CPU: 85.2%, 内存: 2048.5MB, 已处理: 150, 成功: 148, 失败: 2
```

### 处理进度监控
```python
# 块处理进度
处理块 3/10 (50 个日期)
块 3 完成:
  成功: 48, 失败: 2
  耗时: 45.23秒
  平均每日期: 0.90秒
```

## 常见问题

### 1. 内存不足
**症状**: 程序运行缓慢或崩溃
**解决方案**:
- 减少进程数
- 增加chunk_size
- 设置memory_limit_gb

### 2. 处理失败
**症状**: 某些日期处理失败
**解决方案**:
- 检查数据完整性
- 查看错误日志
- 重新运行失败的日期

### 3. 性能不理想
**症状**: 速度提升不明显
**解决方案**:
- 检查CPU使用率
- 调整进程数
- 使用imap_unordered提高效率

## 最佳实践

### 1. 开发阶段
```python
# 使用小数据集测试
prepare_data_mp_optimized(
    start_time="2020-01-01",
    n_processes=2,
    chunk_size=10
)
```

### 2. 生产环境
```python
# 使用完整数据集
prepare_data_mp_optimized(
    start_time="2016-01-01",
    n_processes=8,
    chunk_size=50,
    memory_limit_gb=16
)
```

### 3. 大数据集
```python
# 使用监控版本
prepare_data_mp_with_monitoring(
    n_processes=8,
    monitor_interval=10
)
```

## 输出文件

每个日期会生成以下文件：
- `factor_exp.pkl`: 因子暴露
- `factor_cov.pkl`: 因子协方差
- `specific_risk.pkl`: 特定风险

文件结构：
```
riskdata/
├── 20170101/
│   ├── factor_exp.pkl
│   ├── factor_cov.pkl
│   └── specific_risk.pkl
├── 20170102/
│   ├── factor_exp.pkl
│   ├── factor_cov.pkl
│   └── specific_risk.pkl
└── ...
```

## 依赖包

```bash
pip install multiprocessing
pip install psutil  # 仅监控版本需要
pip install tqdm    # 进度条显示
``` 