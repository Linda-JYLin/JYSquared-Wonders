#!/usr/bin/env python3
import sys
import os

# 添加必要的路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent_code'))
sys.path.insert(0, os.path.dirname(__file__))

try:
    # 测试导入
    from TourSuggester import build_tour_graph, AgentState, datetime
    print("SUCCESS: 导入 TourSuggester 模块")

    # 测试创建图
    graph = build_tour_graph()
    print("SUCCESS: 创建对话图")

    # 测试Flask应用
    from app import app
    print("SUCCESS: 导入 Flask 应用")

    print("\nALL TESTS PASSED! 应用可以正常运行。")
    print("\n启动命令: python run.py")
    print("访问地址: http://localhost:5000")

except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    print("提示: 确保所有依赖已安装 (pip install -r requirements.txt)")

except Exception as e:
    print(f"TEST FAILED: {e}")
    print("请检查相关配置")