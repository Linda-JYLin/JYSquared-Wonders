from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from tour_agent import (
    build_tour_graph, AgentState, datetime,
    tour_guide, attraction_expert, weather_expert,
    restaurant_expert, hotel_expert, transport_expert, budget_expert
)

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

    # 初始化状态
    initial_state = AgentState(
        messages=[{
            "speaker": "System",
            "content": f"欢迎！我已了解您的旅行计划：{data.get('location', '杭州')}，{data.get('days', 3)}天，{data.get('people', 2)}人。正在为您规划行程...",
            "timestamp": datetime.now().isoformat()
        }],
        user_preferences={
            "location": data.get('location', '杭州'),
            "days": data.get('days', 3),
            "people": data.get('people', 2)
        },
        user_suggestions=[],
        current_speaker="TourGuide",
        max_rounds=data.get('max_rounds', 3),
        finished=False,
        round=0
    )

    graph = build_tour_graph()

    conversation_states[session_id] = {
        'state': initial_state,
        'graph': graph
    }

    # 立即运行一次图，生成初始行程建议
    try:
        print(f"[DEBUG] Starting graph invocation for session {session_id}")
        result = graph.invoke(initial_state)
        print(f"[DEBUG] Graph result type: {type(result)}")
        print(f"[DEBUG] Graph result keys: {result.keys() if isinstance(result, dict) else 'N/A'}")

        # LangGraph 直接返回 state，不是 {"state": ...}
        new_state = result if 'messages' in result else result.get('state', result)
        conversation_states[session_id]['state'] = new_state

        # 收集所有AI消息
        ai_messages = []
        for msg in new_state['messages']:
            if msg['speaker'] not in ['System', 'User']:
                ai_messages.append({
                    'content': msg['content'],
                    'speaker': msg['speaker']
                })

        return jsonify({
            'success': True,
            'system_message': initial_state['messages'][0]['content'],
            'ai_messages': ai_messages,
            'finished': new_state.get('finished', False)
        })
    except Exception as e:
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
        user_msg = {
            "speaker": "User",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        }
        state['messages'].append(user_msg)
        state['user_suggestions'].append(user_msg)

    # 运行一个对话轮次
    try:
        print(f"[DEBUG] send_message: Starting graph invocation")
        result = graph.invoke(state)
        print(f"[DEBUG] send_message: Graph completed")

        # LangGraph 直接返回 state
        new_state = result if 'messages' in result else result.get('state', result)

        # 更新状态
        conversation_data['state'] = new_state

        # 收集新生成的AI消息
        ai_messages = []
        for msg in new_state['messages']:
            if msg['speaker'] not in ['System', 'User']:
                ai_messages.append({
                    'content': msg['content'],
                    'speaker': msg['speaker']
                })

        return jsonify({
            'success': True,
            'ai_messages': ai_messages,
            'finished': new_state.get('finished', False)
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

    return jsonify({
        'messages': state['messages'],
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