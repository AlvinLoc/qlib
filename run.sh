source C:/ProgramData/Anaconda3/Scripts/activate qlib
rm -rf mlruns/*
python setup.py install
export PYTHONPATH=.

nohup python mem_monitor.py &
python examples/workflow_by_code_huixian.py