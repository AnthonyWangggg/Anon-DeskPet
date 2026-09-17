"""Optional hardware monitoring; gracefully handles non-NVIDIA computers."""
from __future__ import annotations

import time


def rate(value: float) -> str:
    value = max(0.0, value)
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB/s"


class Metrics:
    def __init__(self):
        try:
            import psutil
            self.psutil = psutil
            psutil.cpu_percent()
        except ImportError:
            self.psutil = None
        self.nvml = self.gpu = None
        self.previous = None
        self.previous_time = 0
        try:
            import pynvml
            pynvml.nvmlInit()
            self.nvml = pynvml
            self.gpu = pynvml.nvmlDeviceGetHandleByIndex(0)
        except Exception:
            pass

    def sample(self) -> str:
        gpu = "不可用"
        if self.gpu is not None:
            try:
                gpu = f"{self.nvml.nvmlDeviceGetUtilizationRates(self.gpu).gpu}%"
            except Exception:
                pass
        if not self.psutil:
            return "系统监测需要安装 psutil"
        net, now = self.psutil.net_io_counters(), time.monotonic()
        up = down = "…"
        if self.previous is not None and net is not None:
            seconds = max(.001, now - self.previous_time)
            up = rate((net.bytes_sent - self.previous.bytes_sent) / seconds)
            down = rate((net.bytes_recv - self.previous.bytes_recv) / seconds)
        self.previous, self.previous_time = net, now
        return (f"CPU    {self.psutil.cpu_percent():.0f}%\n"
                f"内存    {self.psutil.virtual_memory().percent:.0f}%\n"
                f"GPU    {gpu}\n上传    {up}\n下载    {down}")

    def close(self):
        if self.nvml:
            try:
                self.nvml.nvmlShutdown()
            except Exception:
                pass
