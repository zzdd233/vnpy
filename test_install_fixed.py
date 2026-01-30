#!/usr/bin/env python3

# 修复版本的测试脚本，避免日志问题
import os
import sys

# 确保目录存在
os.makedirs('/Users/bytedance/.vntrader/log', exist_ok=True)

# 设置环境变量来避免日志权限问题
os.environ['VT_LOG_PATH'] = '/Users/bytedance/.vntrader/log'

print("正在测试vnpy安装...")

try:
    import vnpy
    print(f"✓ vnpy {vnpy.__version__} 安装成功")
except ImportError as e:
    print(f"✗ 无法导入vnpy: {e}")

try:
    # 先尝试导入基础模块
    from vnpy.event import EventEngine
    from vnpy.trader.engine import MainEngine
    print("✓ vnpy核心模块导入成功")
except ImportError as e:
    print(f"✗ 无法导入vnpy核心模块: {e}")

# 尝试导入其他模块
modules_to_test = [
    ("vnpy_ctastrategy", "CtaStrategyApp"),
    ("vnpy_ctabacktester", "CtaBacktesterApp"),
    ("vnpy_datamanager", "DataManagerApp"),
    ("vnpy_paperaccount", "PaperAccountApp"),
]

for module_name, class_name in modules_to_test:
    try:
        # 使用__import__来动态导入模块
        module = __import__(module_name, fromlist=[class_name])
        getattr(module, class_name)
        print(f"✓ {module_name} 安装成功")
    except ImportError as e:
        print(f"✗ 无法导入{module_name}: {e}")

print("\n安装测试完成！")