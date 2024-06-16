#!python3
# encoding:utf-8

# 1，后台运行，获取kook进程的cpu，内存，GPU 占用率或者数值？
# 2，由于kook有很多进程，希望能做到 分进程统计 并且 计算总值（只能获取总值也行，但是感觉做不到）
# 3，1S获取一次
# 4，写入本地文件，结束后针对数据总值 绘制曲线图（能做成实时绘制的那就更好啦）

from core.kprofiler import KProfiler
import signal


def make_signal_interrupt_handler(profiler: KProfiler):
    def h(sig, frame):
        print("Interrupt signalled, stopping...")
        profiler.notify_stop()
        profiler.wait_all()
        exit(0)

    return h


def main():
    profiler = KProfiler()
    profiler.start()
    signal.signal(signal.SIGINT, make_signal_interrupt_handler(profiler))
    while True:
        pass


if __name__ == "__main__":
    main()
