#!/usr/bin/env python3
"""
测试智能旅游规划助手的基本功能
"""

import sys
import os

# 添加必要的路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent_code'))
sys.path.insert(0, os.path.dirname(__file__))

try:
    # 测试导入
    from TourSuggester import build_tour_graph, AgentState, datetime
    print("✅ 成功导入 TourSuggester 模块")

    # 测试创建图
    graph = build_tour_graph()
    print("✅ 成功创建对话图")

    # 测试初始状态
    initial_state = AgentState(
        messages=[{
            "speaker": "System",
            "content": "测试消息",
            "timestamp": datetime.now().isoformat()
        }],
        user_preferences={
            "location": "杭州",
            "days": 3,
            "people": 2
        },
        user_suggestions=[],
        current_speaker="TourGuide",
        max_rounds=1,
        finished=False
    )
    print("✅ 成功创建初始状态")

    # 测试Flask应用
    from app import app
    print("✅ 成功导入 Flask 应用")

    print("\n🎉 所有测试通过！应用应该可以正常运行。")
    print("\n启动命令: python run.py")
    print("访问地址: http://localhost:5000")

except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("💡 提示: 确保所有依赖已安装 (pip install -r requirements.txt)")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    print("🔧 请检查相关配置")