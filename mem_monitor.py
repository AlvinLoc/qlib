import psutil
import os
import sys
import time
import subprocess
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memory_monitor.log'),
        logging.StreamHandler()
    ]
)

def get_memory_info():
    """获取系统内存信息"""
    memory = psutil.virtual_memory()
    return {
        'total': memory.total,
        'available': memory.available,
        'used': memory.used,
        'percent': memory.percent
    }

def kill_python_processes():
    """终止所有Python进程"""
    killed_count = 0
    
    try:
        # 查找所有Python进程
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # 检查进程名称是否包含python
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    # 排除当前监控进程
                    if proc.pid != psutil.Process().pid:
                        proc.terminate()
                        killed_count += 1
                        logging.warning(f"已终止Python进程 PID: {proc.pid}, 名称: {proc.info['name']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # 如果进程没有正常终止，强制杀死
        time.sleep(2)
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    if proc.pid != psutil.Process().pid:
                        if proc.is_running():
                            proc.kill()
                            logging.warning(f"强制终止Python进程 PID: {proc.pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        logging.info(f"总共终止了 {killed_count} 个Python进程")
        return killed_count
        
    except Exception as e:
        logging.error(f"终止Python进程时发生错误: {e}")
        return 0

def format_memory_size(bytes_size):
    """格式化内存大小显示"""
    gb = bytes_size / (1024**3)
    mb = bytes_size / (1024**2)
    if gb >= 1:
        return f"{gb:.2f} GB"
    else:
        return f"{mb:.2f} MB"

def monitor_memory(threshold_gb=2.0, check_interval=1):
    """
    监控系统内存
    
    Args:
        threshold_gb: 内存阈值（GB），默认1GB
        check_interval: 检查间隔（秒），默认10秒
    """
    threshold_bytes = threshold_gb * (1024**3)
    
    logging.info(f"开始内存监控 - 阈值: {threshold_gb}GB, 检查间隔: {check_interval}秒")
    
    try:
        while True:
            memory_info = get_memory_info()
            available_gb = memory_info['available'] / (1024**3)
            
            logging.info(f"系统内存状态 - 总内存: {format_memory_size(memory_info['total'])}, "
                        f"可用内存: {format_memory_size(memory_info['available'])}, "
                        f"使用率: {memory_info['percent']:.1f}%")
            
            # 检查可用内存是否低于阈值
            if memory_info['available'] < threshold_bytes:
                logging.warning(f"警告！可用内存 ({format_memory_size(memory_info['available'])}) "
                              f"低于阈值 ({threshold_gb}GB)")
                
                killed_count = kill_python_processes()
                
                if killed_count > 0:
                    logging.info("等待系统内存释放...")
                    time.sleep(5)  # 等待内存释放
                    
                    # 再次检查内存状态
                    memory_info_after = get_memory_info()
                    logging.info(f"终止进程后内存状态 - 可用内存: {format_memory_size(memory_info_after['available'])}")
            
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        logging.info("内存监控已停止")
    except Exception as e:
        logging.error(f"监控过程中发生错误: {e}")

def main():
    """主函数"""
    print("Windows内存监控器")
    print("=" * 50)
    print("功能：监控系统剩余内存，当小于1GB时自动终止所有Python进程")
    print("按 Ctrl+C 停止监控")
    print("=" * 50)
    
    try:
        # 直接启动监控，不再检查ACCESS_DENIED
        monitor_memory()
    except Exception as e:
        logging.error(f"程序启动失败: {e}")

def check_mem_monitor():
    """检查mem_monitor.py进程是否在运行"""
    # windows 环境
    if os.name == 'nt':
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info.get('cmdline', [])
                    if any('mem_monitor.py' in arg for arg in cmdline if arg):
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    # linux 环境
    else:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info.get('cmdline', [])
                    if any('mem_monitor.py' in arg for arg in cmdline if arg):
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

if __name__ == "__main__":
    # 检查是否已经开启mem_monitor.py进程
    if False and check_mem_monitor():
        logging.info("mem_monitor.py进程已在运行，跳过启动")
        sys.exit(0)
    else:
        logging.info("mem_monitor.py进程未在运行，启动监控")
    main()
