#!/usr/bin/env python3

# 简单的测试脚本，验证vnpy安装
print("正在测试vnpy安装...")

try:
    import vnpy
    print(f"✓ vnpy {vnpy.__version__} 安装成功")
except ImportError as e:
    print(f"✗ 无法导入vnpy: {e}")

try:
    from vnpy_ctastrategy import CtaStrategyApp
    print("✓ vnpy_ctastrategy 安装成功")
except ImportError as e:
    print(f"✗ 无法导入vnpy_ctastrategy: {e}")

try:
    from vnpy_ctabacktester import CtaBacktesterApp
    print("✓ vnpy_ctabacktester 安装成功")
except ImportError as e:
    print(f"✗ 无法导入vnpy_ctabacktester: {e}")

try:
    from vnpy_datamanager import DataManagerApp
    print("✓ vnpy_datamanager 安装成功")
except ImportError as e:
    print(f"✗ 无法导入vnpy_datamanager: {e}")

try:
    from vnpy_paperaccount import PaperAccountApp
    print("✓ vnpy_paperaccount 安装成功")
except ImportError as e:
    print(f"✗ 无法导入vnpy_paperaccount: {e}")

try:
    from vnpy.event import EventEngine
    from vnpy.trader.engine import MainEngine
    print("✓ vnpy核心模块导入成功")
except ImportError as e:
    print(f"✗ 无法导入vnpy核心模块: {e}")

print("\n安装测试完成！")