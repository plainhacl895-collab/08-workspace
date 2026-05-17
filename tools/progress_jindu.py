# ⚠️【重要】修改本脚本前必须先向佳佳汇报并获得同意，严禁私自修改！
# -*- coding: utf-8 -*-
"""
进度汇报工具 - 每 30 秒自动输出进度，避免卡死错觉
"""
import sys
import time
import threading
from datetime import datetime

class ProgressReporter:
    """进度汇报器 - 每 30 秒自动输出进度"""
    
    def __init__(self, interval=30):
        self.interval = interval  # 汇报间隔（秒）
        self.message = "正在处理..."
        self.running = False
        self.thread = None
        self.start_time = None
    
    def start(self, message="正在处理..."):
        """启动进度汇报"""
        self.message = message
        self.running = True
        self.start_time = datetime.now()
        print(f"[{self._elapsed()}] {self.message}")
        sys.stdout.flush()
        
        # 启动后台线程定时汇报
        self.thread = threading.Thread(target=self._report_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止进度汇报"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
    
    def update(self, message):
        """更新进度消息"""
        self.message = message
        print(f"[{self._elapsed()}] {self.message}")
        sys.stdout.flush()
    
    def _elapsed(self):
        """返回已用时间"""
        if not self.start_time:
            return "0:00"
        elapsed = datetime.now() - self.start_time
        total_seconds = int(elapsed.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def _report_loop(self):
        """后台汇报循环"""
        while self.running:
            time.sleep(self.interval)
            if self.running:
                print(f"[{self._elapsed()}] ⏳ 仍在处理：{self.message}")
                sys.stdout.flush()


# 便捷函数
def report_progress(message, elapsed_seconds):
    """简单进度输出"""
    minutes = elapsed_seconds // 60
    seconds = elapsed_seconds % 60
    print(f"[{minutes}:{seconds:02d}] {message}")
    sys.stdout.flush()


if __name__ == "__main__":
    # 测试
    reporter = ProgressReporter(interval=5)
    reporter.start("测试任务开始")
    
    for i in range(1, 4):
        time.sleep(6)
        reporter.update(f"处理中... 步骤 {i}/3")
    
    time.sleep(2)
    reporter.stop()
    print("✅ 完成")
