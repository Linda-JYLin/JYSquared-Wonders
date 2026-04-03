# 智能旅游规划助手 Web 版本

这是一个基于 TourSuggester 多智能体系统的网页应用，让用户可以通过浏览器与多个AI专家进行对话，制定完美的旅行计划。

## 🌟 功能特点

- **多专家协作**: 7位AI专家协同工作
  - 🧭 导游：协调整个规划流程
  - 🏔️ 景点专家：推荐最佳旅游景点
  - 🌤️ 天气专家：提供天气信息和建议
  - 🍽️ 美食专家：推荐当地特色美食
  - 🏨 住宿专家：推荐合适住宿
  - 🚗 交通专家：规划最佳出行方式
  - 💰 预算专家：估算旅行预算

- **智能对话**: 自然的对话体验，支持上下文理解
- **实时响应**: 即时获取AI专家的建议
- **主题切换**: 支持浅色/深色主题
- **响应式设计**: 适配各种设备屏幕

## 🚀 快速开始

### 1. 安装依赖

```bash
cd agent_web
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python run.py
```

### 3. 访问应用

在浏览器中打开: http://localhost:5000

## 📁 项目结构

```
agent_web/
├── app.py                 # Flask后端应用
├── run.py                 # 启动脚本
├── requirements.txt       # Python依赖
├── templates/
│   └── index.html        # 主页面模板
└── static/
    ├── style.css         # CSS样式
    └── script.js         # JavaScript交互逻辑
```

## 🎮 使用指南

1. **开始对话**: 点击"开始规划"按钮
2. **提供信息**: 告诉AI您的旅行需求（目的地、天数、人数）
3. **获取建议**: 与各个专家对话，获得专业建议
4. **完善计划**: 根据专家建议完善您的旅行计划
5. **新建对话**: 可以开始新的旅行规划

## 💡 使用技巧

- 使用快速操作按钮快速设置目的地、天数、人数
- 按Enter键快速发送消息
- 使用ESC键可以关闭模态框（如果有的话）
- 主题切换按钮在右上角

## 🔧 配置说明

### 修改默认设置
在 `app.py` 中可以修改：
- 默认目的地、天数、人数
- 最大对话轮次
- API配置

### 自定义AI专家
在 `TourSuggester.py` 中可以：
- 添加新的专家类型
- 修改专家提示词
- 调整工具配置

## 🐛 常见问题

### Q: 启动时报错 "ModuleNotFoundError"
A: 确保已安装所有依赖：`pip install -r requirements.txt`

### Q: 无法连接到AI服务
A: 检查 `TourSuggester.py` 中的API密钥配置

### Q: 页面显示不正常
A: 确保使用现代浏览器（Chrome、Firefox、Safari、Edge）

## 📝 注意事项

- 确保 `agent_code/TourSuggester.py` 文件存在且配置正确
- API调用可能需要网络连接
- 对话数据仅在当前会话中保存

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

MIT License