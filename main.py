#!python3
#encoding:utf-8

# 1，后台运行，获取kook进程的cpu，内存，GPU 占用率或者数值？
# 2，由于kook有很多进程，希望能做到 分进程统计 并且 计算总值（只能获取总值也行，但是感觉做不到）
# 3，1S获取一次
# 4，写入本地文件，结束后针对数据总值 绘制曲线图（能做成实时绘制的那就更好啦）

from helpers.gpu_helper import GPUHelper
from helpers.config import Config

def main() -> None:
    config = Config('config.yaml')
    print(config.get_target())

    helper = GPUHelper()
    result = helper.query_process(pid=7944)
    if result is not None:
        process_info, usage = result
        gpu_percent = usage.gpu
        memory_percent = usage.memory
        print(f'GPU: {gpu_percent}%, Memory: {memory_percent}%')

if __name__ == '__main__':
    main()
