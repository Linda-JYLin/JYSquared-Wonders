from datetime import datetime
import json
from typing import Dict, Any

from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_cors import CORS
from langchain_core.messages import HumanMessage, AIMessage

from tour_agent import AgentState, run_tour_agent_stream

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static',
)
CORS(app)

conversation_states: Dict[str, AgentState] = {}


@app.route('/')
def index():
    return render_template('index.html')


def _sse(payload: Dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _build_initial_state(location: str, days: int, people: int) -> AgentState:
    return {
        "messages": [HumanMessage(content=f"我想去{location}玩{days}天，{people}个人，帮我规划一下行程")],
        "user_preferences": {
            "location": location,
            "days": days,
            "people": people,
        },
        "user_suggestions": [],
    }


@app.route('/api/start_conversation', methods=['POST'])
def start_conversation():
    data = request.json or {}
    session_id = data.get('session_id', 'default')
    location = data.get('location', '杭州')
    days = int(data.get('days', 3))
    people = int(data.get('people', 2))

    initial_state = _build_initial_state(location, days, people)
    conversation_states[session_id] = initial_state

    def generate():
        try:
            yield _sse({
                'type': 'system',
                'content': f'欢迎！正在为你规划 {location} 的 {days} 天行程...'
            })

            new_messages = []
            for event in run_tour_agent_stream(initial_state):
                if event.get('type') == 'state':
                    new_messages = event['state'].get('messages', [])
                    continue
                yield _sse(event)

            final_state: AgentState = {
                "messages": initial_state["messages"] + new_messages,
                "user_preferences": initial_state.get("user_preferences", {}),
                "user_suggestions": initial_state.get("user_suggestions", []),
            }
            conversation_states[session_id] = final_state
            yield _sse({'type': 'done'})
        except Exception as exc:
            yield _sse({'type': 'error', 'error': f'生成行程时出错: {exc}'})

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.json or {}
    session_id = data.get('session_id', 'default')
    user_message = data.get('message', '').strip()

    if session_id not in conversation_states:
        return jsonify({'error': '对话未开始，请先开始对话'}), 400

    state = conversation_states[session_id]

    if user_message:
        state['messages'].append(HumanMessage(content=user_message))
        state['user_suggestions'].append({
            'content': user_message,
            'timestamp': datetime.now().isoformat(),
        })

    def generate():
        try:
            new_messages = []
            for event in run_tour_agent_stream(state):
                if event.get('type') == 'state':
                    new_messages = event['state'].get('messages', [])
                    continue
                yield _sse(event)

            final_state: AgentState = {
                "messages": state["messages"] + new_messages,
                "user_preferences": state.get("user_preferences", {}),
                "user_suggestions": state.get("user_suggestions", []),
            }
            conversation_states[session_id] = final_state
            yield _sse({'type': 'done'})
        except Exception as exc:
            yield _sse({'type': 'error', 'error': f'处理消息时出错: {exc}'})

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


@app.route('/api/get_conversation_history', methods=['GET'])
def get_conversation_history():
    session_id = request.args.get('session_id', 'default')

    if session_id not in conversation_states:
        return jsonify({'error': '对话未开始'}), 400

    state = conversation_states[session_id]

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
    session_id = request.args.get('session_id', 'default')

    if session_id in conversation_states:
        del conversation_states[session_id]

    return jsonify({'success': True, 'message': '对话已重置'})


if __name__ == '__main__':
    app.run(debug=True, port=5000)