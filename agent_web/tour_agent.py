from typing import List, Dict, Any, TypedDict
import json
import os
import re
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# 加载环境变量 - 从项目根目录加载
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# 同步到 OPENAI_API_KEY（OpenAI SDK 也需要这个环境变量）
if os.getenv('DEEPSEEK_API_KEY') and not os.getenv('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = os.getenv('DEEPSEEK_API_KEY')

# 初始化模型
def get_llm():
    return ChatOpenAI(
        model=os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
        base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        temperature=0.7,
        request_timeout=60
    )

# ========================
# 工具定义
# ========================

def search_weather(location: str) -> str:
    """查询目的地天气，获取天气信息用于旅行规划"""
    return f"{location}未来三天天气预报：晴天为主，最高气温25°C，最低18°C。"

def search_attractions(location: str) -> str:
    """查询当地景点信息，获取热门旅游景点推荐"""
    results = {
        "北京": "故宫，天安门广场，长城，颐和园，天坛，圆明园，北海公园，南锣鼓巷，鸟巢，雍和宫",
        "上海": "外滩，东方明珠，南京路步行街，豫园，上海迪士尼乐园，田子坊，城隍庙，上海博物馆，新天地，朱家角古镇",
        "广州": "广州塔，沙面岛，陈家祠，越秀公园，白云山，北京路步行街，上下九步行街，圣心大教堂，长隆欢乐世界，珠江夜游",
        "深圳": "世界之窗，欢乐谷，东部华侨城，深圳湾公园，大梅沙海滨公园，锦绣中华民俗村，莲花山公园，华强北，中英街，大鹏所城",
        "成都": "宽窄巷子，锦里，武侯祠，杜甫草堂，青城山，都江堰，大熊猫繁育研究基地，春熙路，文殊院，金沙遗址博物馆",
        "杭州": "西湖，灵隐寺，雷峰塔，西溪湿地，千岛湖，宋城，河坊街，六和塔，九溪十八涧，龙井村",
        "西安": "兵马俑，大雁塔，钟楼，回民街，华清池，大唐不夜城，西安城墙，陕西历史博物馆，华山（附近），法门寺",
        "南京": "中山陵，夫子庙，秦淮河，明孝陵，总统府，玄武湖，南京博物院，栖霞山，鸡鸣寺，雨花台",
        "重庆": "洪崖洞，解放碑，长江索道，磁器口古镇，武隆天生三桥，大足石刻，朝天门，南山一棵树观景台，李子坝轻轨站，白公馆",
        "武汉": "黄鹤楼，东湖，武汉大学（樱花大道），户部巷，湖北省博物馆，长江大桥，归元禅寺，晴川阁，汉口江滩，昙华林",
        "苏州": "拙政园，虎丘，狮子林，留园，周庄古镇，同里古镇，寒山寺，金鸡湖，平江路，苏州博物馆",
        "天津": "天津之眼，五大道，古文化街，意式风情街，瓷房子，盘山，天津滨海航母主题公园，海河游船，南开大学，津湾广场",
        "长沙": "岳麓山，橘子洲头，湖南省博物馆，太平街，天心阁，火宫殿，梅溪湖艺术中心，谢子龙影像艺术馆，长沙世界之窗，马王堆汉墓遗址",
        "青岛": "栈桥，崂山，八大关，五四广场，金沙滩，小青岛，青岛啤酒博物馆，极地海洋世界，天主教堂，奥帆中心",
        "厦门": "鼓浪屿，南普陀寺，厦门大学，曾厝垵，环岛路，中山路步行街，胡里山炮台，植物园，集美学村，沙坡尾",
        "大连": "星海广场，老虎滩海洋公园，金石滩，棒棰岛，滨海路，发现王国主题公园，旅顺口，大连森林动物园，俄罗斯风情街，东港音乐喷泉",
        "昆明": "滇池，石林，翠湖公园，云南民族村，西山森林公园，金马碧鸡坊，官渡古镇，大观楼，九乡溶洞，东川红土地",
        "哈尔滨": "中央大街，圣索菲亚大教堂，冰雪大世界，太阳岛，松花江，哈尔滨极地馆，伏尔加庄园，东北虎林园，老道外，果戈里大街",
        "沈阳": "沈阳故宫，张氏帅府，北陵公园（清昭陵），东陵公园（清福陵），九一八历史博物馆，中街，西塔韩国风情街，辽宁省博物馆，沈阳世博园，棋盘山",
        "洛阳": "龙门石窟，白马寺，老君山，洛阳博物馆，关林，龙潭大峡谷，洛阳老街，白云山，隋唐洛阳城遗址，天子驾六博物馆"
    }
    for key, value in results.items():
        if key in location.lower():
            return value
    return get_llm().invoke(f"给出{location}的十个景点名称。不用列点，输出文字即可。不要输出其他无关文字。").content

def calculate_budget(days: int, people: int) -> str:
    """根据天数和人数估算旅行预算"""
    daily_cost_per_person = 300
    total = days * people * daily_cost_per_person
    return f"预计总预算为 {total} 元（每人每天约300元，包含住宿、餐饮、交通和门票）。"

def search_restaurants(location: str) -> str:
    """查询当地美食推荐，获取特色餐厅和美食信息"""
    return get_llm().invoke(f"给出{location}十样推荐美食名称和十家推荐特色餐厅。不用列点，输出文字即可。不要输出其他无关文字。").content

def search_hotels(location: str) -> str:
    """查询当地酒店推荐，获取不同档次的住宿选择"""
    return get_llm().invoke(f"给出{location}的五个不错的酒店名称（最好是不同档次级别的）。不用列点，输出文字即可。不要输出其他无关文字。").content

def search_transport(location: str) -> str:
    """查询交通方式及路线，获取出行建议"""
    return f"{location}推荐交通：打车+地铁+共享单车，部分景点可步行到达。"

# 工具映射
TOOLS = {
    "search_weather": search_weather,
    "search_attractions": search_attractions,
    "calculate_budget": calculate_budget,
    "search_restaurants": search_restaurants,
    "search_hotels": search_hotels,
    "search_transport": search_transport
}

# ========================
# Agent状态定义
# ========================
class AgentState(TypedDict):
    messages: List[BaseMessage]           # 对话消息
    user_preferences: Dict[str, Any]      # 用户偏好
    user_suggestions: List[Dict[str, str]] # 用户反馈

# ========================
# 导游Agent系统提示
# ========================
TOUR_GUIDE_SYSTEM_PROMPT = """你是一位专业的旅行规划导游，你拥有多种工具来帮助用户规划完美的旅行。

你可以使用以下工具（通过输出JSON格式调用）：
- search_weather: 查询目的地天气，参数: {"tool": "search_weather", "location": "城市名"}
- search_attractions: 查询景点信息，参数: {"tool": "search_attractions", "location": "城市名"}
- calculate_budget: 计算旅行预算，参数: {"tool": "calculate_budget", "days": 天数, "people": 人数}
- search_restaurants: 查询美食餐厅，参数: {"tool": "search_restaurants", "location": "城市名"}
- search_hotels: 查询酒店住宿，参数: {"tool": "search_hotels", "location": "城市名"}
- search_transport: 查询交通方式，参数: {"tool": "search_transport", "location": "城市名"}

调用工具时，单独输出一行JSON，格式如：
{"tool": "工具名", "参数名": "参数值"}

你的职责：
1. 根据用户需求，主动调用相关工具获取信息
2. 整合所有信息，为用户制定详细完整的旅行计划
3. 回答用户关于旅行的问题

制定旅行计划时，请确保：
- 先了解用户的目的地、出行天数、人数等基本信息
- 主动查询天气、景点、美食、住宿、交通和预算
- 最后整合所有信息，给出一个完整的旅行规划建议

请用友好、专业的语气与用户交流。"""

# ========================
# 构建统一的导游Agent
# ========================
def parse_tool_call(content: str) -> tuple:
    """解析内容中的工具调用，返回 (tool_name, args, remaining_content)"""
    # 查找JSON格式的工具调用
    json_pattern = r'\{[^{}]*"tool"\s*:\s*"([^"]+)"[^{}]*\}'
    match = re.search(json_pattern, content)

    if match:
        try:
            json_str = match.group(0)
            tool_call = json.loads(json_str)
            tool_name = tool_call.pop("tool")

            # 移除工具调用JSON，保留其他内容
            remaining = content[:match.start()] + content[match.end():]
            remaining = remaining.strip()

            return tool_name, tool_call, remaining
        except json.JSONDecodeError:
            pass

    return None, None, content

def execute_tool(tool_name: str, args: dict) -> str:
    """执行工具调用"""
    if tool_name not in TOOLS:
        return f"错误：未知工具 '{tool_name}'"

    tool_func = TOOLS[tool_name]
    try:
        return tool_func(**args)
    except Exception as e:
        return f"工具执行错误: {str(e)}"

TOOL_NAMES = {
    "search_weather": "查询天气",
    "search_attractions": "查询景点",
    "calculate_budget": "计算预算",
    "search_restaurants": "查询美食餐厅",
    "search_hotels": "查询酒店",
    "search_transport": "查询交通"
}

def format_tool_call(tool_name: str, args: dict) -> str:
    """将工具调用格式化为友好的文字描述"""
    tool_display = TOOL_NAMES.get(tool_name, tool_name)
    if tool_name == "calculate_budget":
        return f"正在调用工具{tool_display}：{args.get('days', '?')}天，{args.get('people', '?')}人"
    elif "location" in args:
        return f"正在调用工具{tool_display}：{args.get('location', '?')}"
    else:
        args_str = "，".join(f"{k}={v}" for k, v in args.items())
        return f"正在调用工具{tool_display}：{args_str}"

def agent_node(state: AgentState) -> Dict:
    """Agent节点：循环调用工具直到完成任务"""
    messages = list(state["messages"])  # 复制消息列表

    # 构建系统消息
    system_content = TOUR_GUIDE_SYSTEM_PROMPT

    # 如果有用户偏好，添加到上下文
    if state.get("user_preferences"):
        prefs = state["user_preferences"]
        system_content += f"\n\n用户已知偏好信息："
        for k, v in prefs.items():
            system_content += f"\n- {k}: {v}"

    llm = get_llm()
    full_messages = [SystemMessage(content=system_content)] + messages

    # 循环调用工具，最多10次
    max_iterations = 10
    new_messages = []

    for _ in range(max_iterations):
        response = llm.invoke(full_messages)

        # 解析是否有工具调用
        tool_name, tool_args, clean_content = parse_tool_call(response.content)

        if tool_name:
            # 将工具调用转为友好描述
            tool_call_text = format_tool_call(tool_name, tool_args)

            # 替换原响应中的JSON为友好描述
            friendly_response = AIMessage(content=clean_content + "\n" + tool_call_text if clean_content else tool_call_text)
            new_messages.append(friendly_response)

            # 执行工具
            print(f"[INFO] 执行工具: {tool_name}({tool_args})")
            tool_result = execute_tool(tool_name, tool_args)

            # 将工具结果添加到消息，继续循环
            tool_message = HumanMessage(
                content=f"[工具返回结果]\n{tool_result}"
            )
            full_messages = full_messages + [response, tool_message]
            new_messages.append(tool_message)
        else:
            # 没有工具调用，添加响应并结束
            new_messages.append(response)
            break

    return {"messages": new_messages}

def build_tour_guide_agent():
    """构建统一的导游Agent"""

    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("agent", agent_node)

    # 设置入口和出口
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", END)

    return workflow.compile()

# 兼容旧版本的接口
def build_tour_graph():
    """兼容旧版本的接口"""
    return build_tour_guide_agent()

# ========================
# 便捷调用函数
# ========================
def run_tour_guide(user_input: str, preferences: Dict = None, history: List[BaseMessage] = None) -> str:
    """
    运行导游Agent的便捷函数

    Args:
        user_input: 用户输入
        preferences: 用户偏好（可选）
        history: 历史对话（可选）

    Returns:
        导游的回复
    """
    agent = build_tour_guide_agent()

    messages = history or []
    messages.append(HumanMessage(content=user_input))

    initial_state = {
        "messages": messages,
        "user_preferences": preferences or {},
        "user_suggestions": []
    }

    result = agent.invoke(initial_state)

    # 返回最后一条AI消息
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            return msg.content

    return "抱歉，我无法生成回复。"


# ========================
# 测试代码
# ========================
if __name__ == "__main__":
    # 测试导游Agent
    agent = build_tour_guide_agent()

    # 模拟用户输入
    test_state = {
        "messages": [HumanMessage(content="我想去北京玩3天，2个人，帮我规划一下行程")],
        "user_preferences": {
            "location": "北京",
            "days": 3,
            "people": 2
        },
        "user_suggestions": []
    }

    print("正在规划旅行...\n")
    result = agent.invoke(test_state)

    # 打印所有消息
    for msg in result["messages"]:
        if isinstance(msg, AIMessage):
            print(f"导游: {msg.content}\n")
        elif isinstance(msg, HumanMessage):
            print(f"用户: {msg.content}\n")
