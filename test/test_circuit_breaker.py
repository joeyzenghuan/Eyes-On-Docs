"""
测试熔断机制：2分钟内发送超过20次error通知时，程序应自动退出

测试方法：
1. 设置较小的阈值进行快速测试
2. 模拟连续发送error日志
3. 验证熔断机制是否正确触发
"""

import sys
import os

# 添加父目录到路径，以便导入logs模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 在导入logs之前，设置测试用的环境变量（降低阈值以便快速测试）
os.environ['ERROR_WINDOW_SECONDS'] = '60'  # 1分钟时间窗口
os.environ['ERROR_THRESHOLD'] = '5'  # 降低到5次以便快速测试
# os.environ['ERROR_WEBHOOK_URL'] = 'your_test_webhook_url'  # 如需测试实际webhook，取消注释并填入URL

import time

def test_circuit_breaker_trigger():
    """测试熔断机制触发"""
    # 重新导入以应用新的环境变量
    import importlib
    import logs
    importlib.reload(logs)
    
    from logs import logger, ERROR_WINDOW_SECONDS, ERROR_THRESHOLD
    
    print(f"\n{'='*60}")
    print(f"熔断机制测试")
    print(f"时间窗口: {ERROR_WINDOW_SECONDS} 秒")
    print(f"触发阈值: {ERROR_THRESHOLD} 次")
    print(f"{'='*60}\n")
    
    print("开始发送error日志，预期在第{}次时触发熔断...\n".format(ERROR_THRESHOLD))
    
    for i in range(ERROR_THRESHOLD + 5):  # 多发几次确保触发
        print(f"[{i+1}] 发送error日志...")
        logger.error(f"测试异常 #{i+1}: 这是一个模拟的错误消息")
        time.sleep(0.5)  # 稍微间隔一下，避免太快
    
    # 如果程序运行到这里，说明熔断机制没有触发
    print("\n❌ 测试失败：熔断机制未触发，程序应该已经退出")


def test_no_trigger_under_threshold():
    """测试阈值内不触发熔断"""
    import importlib
    import logs
    importlib.reload(logs)
    
    from logs import logger, ERROR_WINDOW_SECONDS, ERROR_THRESHOLD
    
    print(f"\n{'='*60}")
    print(f"测试阈值内不触发熔断")
    print(f"时间窗口: {ERROR_WINDOW_SECONDS} 秒")
    print(f"触发阈值: {ERROR_THRESHOLD} 次")
    print(f"发送次数: {ERROR_THRESHOLD - 1} 次（低于阈值）")
    print(f"{'='*60}\n")
    
    for i in range(ERROR_THRESHOLD - 1):  # 发送少于阈值的次数
        print(f"[{i+1}] 发送error日志...")
        logger.error(f"测试异常 #{i+1}: 这是一个模拟的错误消息")
        time.sleep(0.3)
    
    print("\n✅ 测试通过：发送了{}次error，未触发熔断（阈值为{}）".format(
        ERROR_THRESHOLD - 1, ERROR_THRESHOLD))


def test_window_expiry():
    """测试时间窗口过期后计数重置"""
    # 设置更短的时间窗口用于测试
    os.environ['ERROR_WINDOW_SECONDS'] = '5'  # 5秒时间窗口
    os.environ['ERROR_THRESHOLD'] = '3'  # 3次阈值
    
    import importlib
    import logs
    importlib.reload(logs)
    
    from logs import logger, ERROR_WINDOW_SECONDS, ERROR_THRESHOLD
    
    print(f"\n{'='*60}")
    print(f"测试时间窗口过期")
    print(f"时间窗口: {ERROR_WINDOW_SECONDS} 秒")
    print(f"触发阈值: {ERROR_THRESHOLD} 次")
    print(f"{'='*60}\n")
    
    # 发送2次（低于阈值）
    for i in range(2):
        print(f"[第一批 {i+1}] 发送error日志...")
        logger.error(f"第一批测试异常 #{i+1}")
        time.sleep(0.2)
    
    print(f"\n等待 {ERROR_WINDOW_SECONDS + 1} 秒让时间窗口过期...\n")
    time.sleep(ERROR_WINDOW_SECONDS + 1)
    
    # 再发送2次（由于时间窗口过期，之前的记录应该被清除）
    for i in range(2):
        print(f"[第二批 {i+1}] 发送error日志...")
        logger.error(f"第二批测试异常 #{i+1}")
        time.sleep(0.2)
    
    print("\n✅ 测试通过：时间窗口过期后计数重置，未触发熔断")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("熔断机制测试套件")
    print("="*60)
    
    # 检查是否配置了webhook URL
    if not os.getenv('ERROR_WEBHOOK_URL'):
        print("\n⚠️  警告: ERROR_WEBHOOK_URL 未设置")
        print("   熔断机制仍会生效，但不会实际发送Teams通知")
        print("   如需测试实际通知，请设置 ERROR_WEBHOOK_URL 环境变量\n")
    
    print("\n请选择测试:")
    print("1. 测试熔断触发（程序会退出）")
    print("2. 测试阈值内不触发")
    print("3. 测试时间窗口过期")
    print("4. 运行所有测试（先运行2和3，最后运行1）")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    if choice == '1':
        test_circuit_breaker_trigger()
    elif choice == '2':
        test_no_trigger_under_threshold()
    elif choice == '3':
        test_window_expiry()
    elif choice == '4':
        print("\n" + "-"*40)
        print("运行测试 2: 阈值内不触发")
        print("-"*40)
        test_no_trigger_under_threshold()
        
        print("\n" + "-"*40)
        print("运行测试 3: 时间窗口过期")
        print("-"*40)
        test_window_expiry()
        
        print("\n" + "-"*40)
        print("运行测试 1: 熔断触发（程序将退出）")
        print("-"*40)
        test_circuit_breaker_trigger()
    else:
        print("无效选择")
