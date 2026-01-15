import sys
from datetime import datetime
from loguru import logger as _logger
from dotenv import load_dotenv
import os
import requests
from collections import deque
import time

# from metagpt.const import PROJECT_ROOT

load_dotenv(override=True)  # 允许覆盖环境变量  # 加载.env文件中的环境变量
ERROR_WEBHOOK_URL = os.getenv('ERROR_WEBHOOK_URL')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # 从环境变量读取日志级别，默认为 INFO

# 熔断配置：2分钟内超过20次error通知则退出程序
ERROR_WINDOW_SECONDS = int(os.getenv('ERROR_WINDOW_SECONDS', 120))  # 时间窗口（秒）
ERROR_THRESHOLD = int(os.getenv('ERROR_THRESHOLD', 20))  # 阈值

class WebhookHandler:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.error_timestamps = deque()  # 记录error发送时间戳
        self.window_seconds = ERROR_WINDOW_SECONDS
        self.threshold = ERROR_THRESHOLD

    def _cleanup_old_timestamps(self):
        """清理超出时间窗口的旧时间戳"""
        current_time = time.time()
        while self.error_timestamps and (current_time - self.error_timestamps[0]) > self.window_seconds:
            self.error_timestamps.popleft()

    def _check_circuit_breaker(self):
        """检查是否触发熔断机制"""
        self._cleanup_old_timestamps()
        if len(self.error_timestamps) >= self.threshold:
            print(f"\n{'='*60}")
            print(f"[熔断机制触发] 在 {self.window_seconds} 秒内发送了 {len(self.error_timestamps)} 次error通知")
            print(f"超过阈值 {self.threshold}，程序将退出以防止通知风暴")
            print(f"{'='*60}\n")
            # 发送最后一条通知告知熔断
            try:
                requests.post(self.webhook_url, json={
                    'text': f"⚠️ 熔断机制触发：{self.window_seconds}秒内发送了{len(self.error_timestamps)}次error通知，程序已自动退出。请检查系统状态。"
                })
            except:
                pass
            os._exit(1)  # 强制退出程序

    def __call__(self, message):
        # print(f"message: {message}")
        try:
            # 解析消息中的异常信息
            if "Traceback" in message or "ERROR" in message:
                # 记录当前时间戳
                self.error_timestamps.append(time.time())
                
                # 检查是否触发熔断
                self._check_circuit_breaker()
                
                # 发送异常通知到webhook URL
                # print(f"检测到异常：\n{message}")
                requests.post(self.webhook_url, json={'text': f"检测到异常：\n{message}"})
        except Exception as e:
            # 处理webhook发送失败的情况
            print(f"发送webhook通知失败: {str(e)}")

def define_log_level(print_level=LOG_LEVEL, logfile_level=LOG_LEVEL):
    """调整日志级别到level之上
       Adjust the log level to above level
    """
    _logger.remove()
    _logger.add(sys.stderr, level=print_level)
    # _logger.add(PROJECT_ROOT / 'logs/log.txt', level=logfile_level)
    
    # 生成包含时间戳的日志文件名
    current_time = datetime.now().strftime("%Y%m%d_%H%M")
    log_filename = f'logs/log_{current_time}.txt'
    
    # 确保logs目录存在
    os.makedirs('logs', exist_ok=True)
    _logger.add(log_filename, level=logfile_level)
    
    if ERROR_WEBHOOK_URL:
        _logger.add(WebhookHandler(ERROR_WEBHOOK_URL), level="ERROR")
    
    return _logger

logger = define_log_level()

# 测试代码
if __name__ == "__main__":
    # 测试普通日志
    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    
    # 测试错误日志和webhook通知
    try:
        # 制造一个异常
        result = 1 / 0
    except Exception as e:
        logger.error(f"发生除零错误: {str(e)}")
        
    # 测试不同级别的日志
    test_logger = define_log_level(print_level="DEBUG", logfile_level="DEBUG")
    test_logger.debug("测试自定义级别的调试日志")
