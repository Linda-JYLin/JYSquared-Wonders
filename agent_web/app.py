from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
from tour_agent import build_tour_graph, AgentState

app = Flask(__name__,
                template_folder='templates',
                static_folder='static',
                static_url_path='/static')
CORS(app)

# 全局变量存储对话状态
conversation_states = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start_conversation', methods=['POST'])
def start_conversation():
    """开始新的对话"""
    data = request.json
    session_id = data.get('session_id', 'default')

    location = data.get('location', '杭州')
    days = data.get('days', 3)
    people = data.get('people', 2)

    # 初始化状态
    initial_state = {
        "messages": [HumanMessage(content=f"我想去{location}玩{days}天，{people}个人，帮我规划一下行程")],
        "user_preferences": {
            "location": location,
            "days": days,
            "people": people
        },
        "user_suggestions": []
    }

    graph = build_tour_graph()

    conversation_states[session_id] = {
        'state': initial_state,
        'graph': graph
    }

    # 运行agent生成行程建议
    try:
        print(f"[DEBUG] Starting agent invocation for session {session_id}")
        result = graph.invoke(initial_state)
        print(f"[DEBUG] Agent result type: {type(result)}")

        # 更新状态
        conversation_states[session_id]['state'] = result

        # 收集AI消息
        ai_messages = []
        for msg in result['messages']:
            if isinstance(msg, AIMessage):
                ai_messages.append({
                    'content': msg.content,
                    'speaker': '导游'
                })

        return jsonify({
            'success': True,
            'system_message': f"欢迎！正在为您规划{location}的{days}天行程...",
            'ai_messages': ai_messages
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'生成行程时出错: {str(e)}'}), 500

@app.route('/api/send_message', methods=['POST'])
def send_message():
    """发送用户消息并获取AI响应"""
    data = request.json
    session_id = data.get('session_id', 'default')
    user_message = data.get('message', '')

    if session_id not in conversation_states:
        return jsonify({'error': '对话未开始，请先开始对话'}), 400

    conversation_data = conversation_states[session_id]
    state = conversation_data['state']
    graph = conversation_data['graph']

    # 添加用户消息到状态
    if user_message:
        state['messages'].append(HumanMessage(content=user_message))
        state['user_suggestions'].append({
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })

    # 运行agent
    try:
        print(f"[DEBUG] send_message: Starting agent invocation")
        result = graph.invoke(state)
        print(f"[DEBUG] send_message: Agent completed")

        # 更新状态
        conversation_data['state'] = result

        # 收集AI消息
        ai_messages = []
        for msg in result['messages']:
            if isinstance(msg, AIMessage):
                ai_messages.append({
                    'content': msg.content,
                    'speaker': '导游'
                })

        return jsonify({
            'success': True,
            'ai_messages': ai_messages
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'处理消息时出错: {str(e)}'}), 500

@app.route('/api/get_conversation_history', methods=['GET'])
def get_conversation_history():
    """获取对话历史"""
    session_id = request.args.get('session_id', 'default')

    if session_id not in conversation_states:
        return jsonify({'error': '对话未开始'}), 400

    state = conversation_states[session_id]['state']

    # 转换消息格式
    messages = []
    for msg in state['messages']:
        if isinstance(msg, HumanMessage):
            messages.append({'speaker': 'User', 'content': msg.content})
        elif isinstance(msg, AIMessage):
            messages.append({'speaker': '导游', 'content': msg.content})

    return jsonify({
        'messages': messages,
        'user_suggestions': state['user_suggestions'],
        'user_preferences': state['user_preferences']
    })

@app.route('/api/reset_conversation', methods=['POST'])
def reset_conversation():
    """重置对话"""
    session_id = request.args.get('session_id', 'default')

    if session_id in conversation_states:
        del conversation_states[session_id]

    return jsonify({'success': True, 'message': '对话已重置'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
