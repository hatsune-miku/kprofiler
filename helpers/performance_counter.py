from utils import platform

if platform.is_macos():
    from . import performance_counter_virtual

    PerformanceCounter = performance_counter_virtual.PerformanceCounter
else:
    from . import performance_counter_win

    PerformanceCounter = performance_counter_win.PerformanceCounter
