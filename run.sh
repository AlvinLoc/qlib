source C:/ProgramData/Anaconda3/Scripts/activate qlib
rm -rf mlruns/*
# # python setup.py install

# # 卸载现有的qlib包
# pip uninstall qlib -y
# pip uninstall pyqlib -y

# # 重新安装qlib包
# pip install -e .
export PYTHONPATH=.

# python mem_monitor.py &
python examples/workflow_by_code_huixian.py
# C:\Users\ZHX\.qlib\qlib_data\cn_data\instruments\refine_all.txt
cp ~/.qlib/qlib_data/cn_data/instruments/refine_all.txt ~/.qlib/qlib_data/cn_data/instruments/all.txt 