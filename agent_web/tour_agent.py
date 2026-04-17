from typing import Any, Dict, Iterator, List, TypedDict
import json
import os
import re
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END


env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

if os.getenv('DEEPSEEK_API_KEY') and not os.getenv('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = os.getenv('DEEPSEEK_API_KEY')


class AgentState(TypedDict):
    messages: List[BaseMessage]
    user_preferences: Dict[str, Any]
    user_suggestions: List[Dict[str, str]]


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
        base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        temperature=0.7,
        request_timeout=60,
    )


def search_weather(location: str) -> str:
    return f"{location}未来三天天气：以晴到多云为主，早晚温差较大，建议携带薄外套。"


def search_attractions(location: str) -> str:
    return get_llm().invoke(
        f"请给出{location}10个热门景点名称，并各用一句话说明特色。仅输出结果，不要额外解释。"
    ).content


def calculate_budget(days: int, people: int) -> str:
    daily_cost_per_person = 300
    total = days * people * daily_cost_per_person
    return f"预计总预算约 {total} 元（按每人每天约 {daily_cost_per_person} 元估算）。"


def search_restaurants(location: str) -> str:
    return get_llm().invoke(
        f"请给出{location}10种推荐美食和10家推荐餐厅。仅输出结果，不要额外解释。"
    ).content


def search_hotels(location: str) -> str:
    return get_llm().invoke(
        f"请给出{location}5家不同价位酒店推荐，并各一句话说明适合人群。仅输出结果。"
    ).content


def search_transport(location: str) -> str:
    return f"{location}推荐交通：地铁/公交 + 网约车组合，跨区优先高铁或城际，景区周边建议步行。"


TOOLS = {
    "search_weather": search_weather,
    "search_attractions": search_attractions,
    "calculate_budget": calculate_budget,
    "search_restaurants": search_restaurants,
    "search_hotels": search_hotels,
    "search_transport": search_transport,
}


TOUR_GUIDE_SYSTEM_PROMPT = """你是一位专业且友好的旅行规划导游。
你可以在需要时调用以下工具（通过输出一行 JSON 调用）：
- search_weather: {"tool":"search_weather","location":"城市名"}
- search_attractions: {"tool":"search_attractions","location":"城市名"}
- calculate_budget: {"tool":"calculate_budget","days":天数,"people":人数}
- search_restaurants: {"tool":"search_restaurants","location":"城市名"}
- search_hotels: {"tool":"search_hotels","location":"城市名"}
- search_transport: {"tool":"search_transport","location":"城市名"}

当你要调用工具时，请只输出一行 JSON，不要加解释。
当信息足够时，请输出完整旅行建议，包含：
1) 每日行程安排
2) 餐饮建议
3) 住宿建议
4) 交通建议
5) 预算建议
"""


TOOL_NAMES = {
    "search_weather": "查询天气",
    "search_attractions": "查询景点",
    "calculate_budget": "计算预算",
    "search_restaurants": "查询美食餐厅",
    "search_hotels": "查询酒店",
    "search_transport": "查询交通",
}


def parse_tool_call(content: str):
    json_pattern = r'\{[^{}]*"tool"\s*:\s*"([^"]+)"[^{}]*\}'
    match = re.search(json_pattern, content)
    if not match:
        return None, None, content

    try:
        json_str = match.group(0)
        tool_call = json.loads(json_str)
        tool_name = tool_call.pop("tool")
        remaining = (content[:match.start()] + content[match.end():]).strip()
        return tool_name, tool_call, remaining
    except json.JSONDecodeError:
        return None, None, content


def execute_tool(tool_name: str, args: Dict[str, Any]) -> str:
    if tool_name not in TOOLS:
        return f"工具不存在: {tool_name}"
    try:
        return TOOLS[tool_name](**args)
    except Exception as exc:
        return f"工具执行失败: {exc}"


def format_tool_call(tool_name: str, args: Dict[str, Any]) -> str:
    tool_display = TOOL_NAMES.get(tool_name, tool_name)
    if tool_name == "calculate_budget":
        return f"正在调用工具 {tool_display}：{args.get('days', '?')} 天，{args.get('people', '?')} 人"
    if "location" in args:
        return f"正在调用工具 {tool_display}：{args.get('location', '?')}"
    args_str = ", ".join(f"{k}={v}" for k, v in args.items())
    return f"正在调用工具 {tool_display}：{args_str}"


def _build_system_prompt(state: AgentState) -> str:
    system_content = TOUR_GUIDE_SYSTEM_PROMPT
    prefs = state.get("user_preferences") or {}
    if prefs:
        lines = ["\n\n已知用户偏好："]
        for k, v in prefs.items():
            lines.append(f"- {k}: {v}")
        system_content += "\n".join(lines)
    return system_content


def _extract_text_from_chunk(chunk: Any) -> str:
    if chunk is None:
        return ""
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts: List[str] = []
        for item in content:
            if isinstance(item, str):
                texts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                texts.append(item.get("text", ""))
        return "".join(texts)
    return str(content)


def _run_agent_messages(state: AgentState) -> List[BaseMessage]:
    messages = list(state["messages"])
    system_content = _build_system_prompt(state)

    llm = get_llm()
    full_messages = [SystemMessage(content=system_content)] + messages

    max_iterations = 10
    new_messages: List[BaseMessage] = []

    for _ in range(max_iterations):
        response = llm.invoke(full_messages)
        tool_name, tool_args, clean_content = parse_tool_call(response.content)

        if tool_name:
            if clean_content:
                new_messages.append(AIMessage(content=clean_content))
            tool_status_text = format_tool_call(tool_name, tool_args)
            new_messages.append(AIMessage(content=tool_status_text))
            tool_result = execute_tool(tool_name, tool_args)
            tool_message = HumanMessage(content=f"[工具返回结果]\n{tool_result}")
            full_messages = full_messages + [response, tool_message]
            new_messages.append(tool_message)
            continue

        new_messages.append(response)
        break

    return new_messages


def agent_node(state: AgentState) -> Dict[str, List[BaseMessage]]:
    return {"messages": _run_agent_messages(state)}


def run_tour_agent_stream(state: AgentState) -> Iterator[Dict[str, Any]]:
    messages = list(state["messages"])
    system_content = _build_system_prompt(state)
    llm = get_llm()
    full_messages = [SystemMessage(content=system_content)] + messages

    max_iterations = 10
    new_messages: List[BaseMessage] = []

    for _ in range(max_iterations):
        response = llm.invoke(full_messages)
        tool_name, tool_args, clean_content = parse_tool_call(response.content)

        if tool_name:
            if clean_content:
                clean_msg = AIMessage(content=clean_content)
                new_messages.append(clean_msg)
                yield {
                    "type": "message",
                    "content": clean_content,
                    "speaker": "导游",
                }

            tool_status_text = format_tool_call(tool_name, tool_args)
            tool_status_msg = AIMessage(content=tool_status_text)
            new_messages.append(tool_status_msg)
            yield {
                "type": "tool_status",
                "content": tool_status_text,
                "speaker": "导游",
            }

            tool_result = execute_tool(tool_name, tool_args)
            tool_message = HumanMessage(content=f"[工具返回结果]\n{tool_result}")
            full_messages = full_messages + [response, tool_message]
            new_messages.append(tool_message)
            continue

        # Final response streamed by chunks
        streamed_text = ""
        yield {"type": "ai_start", "speaker": "导游"}
        try:
            for chunk in llm.stream(full_messages):
                text_piece = _extract_text_from_chunk(chunk)
                if not text_piece:
                    continue

                # Character-level flush for visible streaming effect
                for char in text_piece:
                    streamed_text += char
                    yield {
                        "type": "ai_chunk",
                        "chunk": char,
                        "speaker": "导游",
                    }
        except Exception:
            streamed_text = ""

        if not streamed_text:
            streamed_text = response.content or ""
            for char in streamed_text:
                yield {
                    "type": "ai_chunk",
                    "chunk": char,
                    "speaker": "导游",
                }

        new_messages.append(AIMessage(content=streamed_text))
        yield {"type": "ai_end", "speaker": "导游"}
        break

    updated_state: AgentState = {
        "messages": new_messages,
        "user_preferences": state.get("user_preferences", {}),
        "user_suggestions": state.get("user_suggestions", []),
    }
    yield {"type": "state", "state": updated_state}


def build_tour_guide_agent():
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", END)
    return workflow.compile()


def build_tour_graph():
    return build_tour_guide_agent()


def run_tour_guide(user_input: str, preferences: Dict = None, history: List[BaseMessage] = None) -> str:
    agent = build_tour_guide_agent()
    messages = history or []
    messages.append(HumanMessage(content=user_input))

    initial_state: AgentState = {
        "messages": messages,
        "user_preferences": preferences or {},
        "user_suggestions": [],
    }

    result = agent.invoke(initial_state)
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            return msg.content
    return "抱歉，我暂时无法生成建议。"