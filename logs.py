import sys
from datetime import datetime
from loguru import logger as _logger
from dotenv import load_dotenv
import os
import requests

# from metagpt.const import PROJECT_ROOT

load_dotenv()  # 加载.env文件中的环境变量
ERROR_WEBHOOK_URL = os.getenv('ERROR_WEBHOOK_URL')

class WebhookHandler:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def __call__(self, message):
        # print(f"message: {message}")
        try:
            # 解析消息中的异常信息
            if "Traceback" in message or "ERROR" in message:
                # 发送异常通知到webhook URL
                # print(f"检测到异常：\n{message}")
                requests.post(self.webhook_url, json={'text': f"检测到异常：\n{message}"})
        except Exception as e:
            # 处理webhook发送失败的情况
            print(f"发送webhook通知失败: {str(e)}")

def define_log_level(print_level="INFO", logfile_level="INFO"):
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
