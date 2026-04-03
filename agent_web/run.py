#!/usr/bin/env python3
"""
智能旅游规划助手 - 启动脚本
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app

if __name__ == '__main__':
    print("🚀 启动智能旅游规划助手...")
    print("🌐 访问地址: http://localhost:5000")
    print("📱 在浏览器中打开上述地址开始使用")
    print("🔄 按 Ctrl+C 停止服务")

    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 提示: 确保已安装所有依赖 (pip install -r requirements.txt)")