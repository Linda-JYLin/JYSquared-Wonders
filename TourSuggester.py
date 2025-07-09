from typing import List, Dict, Any, Annotated, Sequence, Literal, TypedDict, Union
from datetime import datetime
import operator
import json
import os
#from dotenv import load_dotenv

from IPython.display import Image, display
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool

from langgraph.types import Command, interrupt
# # 加载环境变量
# load_dotenv()

# 初始化DeepSeek模型
model = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key="sk-ef26a3f6e17a4d85ab99e4e2d89fb8e4",
    temperature=0.7
)

# ========================
# 工具定义
# ========================

@tool
def search_weather(location: str) -> str:
    """模拟查询目的地天气"""
    return f"{location}未来三天天气预报：晴天为主，最高气温25°C，最低18°C。"

@tool
def search_attractions(location: str) -> str:
    """模拟查询当地景点信息"""
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
            # print(f"检索到：{value}\n")
            return value
    value = model.invoke(f"给出{location}的十个景点名称。不用列点，输出文字即可。不要输出其他无关文字。").content
    # print(f"\n检索到：{value}\n")
    return value

@tool
def calculate_budget(days: int, people: int) -> str:
    """根据天数和人数估算旅行预算"""
    daily_cost_per_person = 300
    total = days * people * daily_cost_per_person
    return f"预计总预算为 {total} 元（每人每天约300元）。"

@tool
def search_restaurants(location: str) -> str:
    """模拟查询当地美食推荐"""
    return model.invoke(f"给出{location}十样推荐美食名称和十家推荐特色餐厅。不用列点，输出文字即可。不要输出其他无关文字。").content

@tool
def search_hotels(location: str) -> str:
    """模拟查询当地酒店推荐"""
    return model.invoke(f"给出{location}的五个不错的酒店名称（最好是不同档次级别的）。不用列点，输出文字即可。不要输出其他无关文字。").content

@tool
def search_transport(location: str) -> str:
    """模拟查询交通方式及路线"""
    return f"{location}推荐交通：打车+地铁+共享单车，部分景点可步行到达。"

# 人类互动
@tool
def human_feedback():
    """收集用户在命令行输入的反馈内容。用于导游节点向用户提问并等待回答。"""
    feedback = input("\n请提供您的反馈或回答问题（直接回车跳过）: ").strip()
    if feedback:
        print(f"您输入的内容是: {feedback}")
        return feedback
    else:
        return "用户未提供反馈。"

# 创建搜索工具实例
tools = {
    "weather": search_weather,
    "attractions": search_attractions,
    "budget": calculate_budget,
    "restaurants": search_restaurants,
    "hotels": search_hotels,
    "transport": search_transport,
    "human":human_feedback
}

# ========================
# Agent状态定义
# ========================
class AgentState(TypedDict):
    messages: List[Dict[str, str]]         # 短期记忆：对话记录
    user_preferences: Dict[str, Any]       # 长期记忆：用户偏好
    user_suggestions: List[Dict[str, str]]  # 长期记忆：用户反馈
    current_speaker: str
    max_rounds: int
    finished: bool

# ========================
# 工具
# ========================
# 轮次
ROUND = 0
def print_memory(state: AgentState):
    print("\n=== 当前记忆状态 ===\n")

    # 短期记忆：messages
    print("【短期记忆 - messages】")
    for msg in state["messages"]:
        print(f"{msg['speaker']}: {msg['content']}")

    print("\n【长期记忆 - user_preferences】")
    for k, v in state["user_preferences"].items():
        print(f"{k}: {v}")

    print("\n【长期记忆 - user_suggestions】")
    for msg in state["user_suggestions"]:
        print(f"{msg['speaker']}: {msg['content']}")

    print("\n=========================\n")

# ========================
# 智能体类定义
# ========================

class TourAgent:
    def __init__(self, name: str, role: str, system_prompt: str, tools_used: List[str]):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.tools_used = tools_used
        self.memory: List[Dict] = []

    def update_memory(self, message: Dict):
        self.memory.append(message)

    def get_context(self, state: AgentState) -> str:
        history = "\n".join([f"{m['speaker']}: {m['content']}" for m in state["messages"][-7:]])
        preferences = "\n".join([f"{k}: {v}" for k, v in state["user_preferences"].items()])
        suggestions = "\n".join([f"{m['speaker']}: {m['content']}" for m in state["user_suggestions"]])
        return f"""
{self.system_prompt}

用户偏好：
{preferences}{suggestions}

对话历史：
{history}

现在轮到你发言，请根据以上信息继续讨论。
"""

# ========================
# 创建各智能体实例
# ========================

tour_guide = TourAgent(
    "TourGuide",
    "moderator",
    "你是旅行团的导游，首先负责总结信息给出完整而详细的旅行行程，然后协调各个专家完善细节，最后可以引导用户完成旅行规划。",
    tools_used=["human"]
)

attraction_expert = TourAgent(
    "AttractionExpert",
    "expert",
    "你是景点专家，只专注负责推荐合适的旅游景点，并说明理由。如果用户意见涉及到景点才回答他，不要涉及其他类别。",
    tools_used=["attractions"]
)

weather_expert = TourAgent(
    "WeatherExpert",
    "expert",
    "你是天气专家，只专注负责提供目的地的天气情况，以便做出合理安排。如果用户意见涉及到天气才回答他，不要涉及其他类别。",
    tools_used=["weather"]
)

restaurant_expert = TourAgent(
    "RestaurantExpert",
    "expert",
    "你是美食专家，只专注负责推荐当地特色餐厅和美食。如果用户意见涉及到美食才回答他，不要涉及其他类别。",
    tools_used=["restaurants"]
)

hotel_expert = TourAgent(
    "HotelExpert",
    "expert",
    "你是住宿专家，只专注负责推荐适合的酒店或民宿。如果用户意见涉及到住宿才回答他，不要涉及其他类别。",
    tools_used=["hotels"]
)

transport_expert = TourAgent(
    "TransportExpert",
    "expert",
    "你是交通专家，只专注负责推荐最佳出行方式。如果用户意见涉及到交通才回答他，不要涉及其他类别。",
    tools_used=["transport"]
)

budget_expert = TourAgent(
    "BudgetExpert",
    "expert",
    "你是财务专家，只专注负责预算估算。如果用户意见涉及到预算和消费才回答他，不要涉及其他类别。",
    tools_used=["budget"]
)

agents = {
    "TourGuide": tour_guide,
    "AttractionExpert": attraction_expert,
    "WeatherExpert": weather_expert,
    "RestaurantExpert": restaurant_expert,
    "HotelExpert": hotel_expert,
    "TransportExpert": transport_expert,
    "BudgetExpert": budget_expert
}

# ========================
# 节点函数定义
# ========================
def guide_node(state: AgentState) -> Dict:
    global ROUND
    ROUND = ROUND + 1
    print(f"\n======================ROUND {ROUND}======================")
    context = agents["TourGuide"].get_context(state)
    response = model.invoke([HumanMessage(content=context)])
    msg = {"speaker": "TourGuide", "content": response.content, "timestamp": datetime.now().isoformat()}
    state["messages"].append(msg) # 添加自己的短期记忆

    print(f"\n🧠🧠**TourGuide:**\n{response.content}")

    # 使用 human_feedback 工具获取用户反馈
    feedback = tools["human"].invoke({})
    if feedback and "用户未提供反馈" not in feedback:
        feedback_msg = {
            "speaker": "User",
            "content": feedback,
            "timestamp": datetime.now().isoformat()
        }
        state["user_suggestions"].append(feedback_msg)

    if ROUND >= state["max_rounds"]:
        # print("It's END!\n")
        state["finished"] = True
        return {"state": state, "next": END}  # 达到3轮后结束
    else:
        # print("Continue.")
        return {"state": state, "next": "AttractionExpert"}


def attraction_node(state: AgentState) -> Dict:
    context = agents["AttractionExpert"].get_context(state)
    tool_response = tools["attractions"].invoke(state["user_preferences"]["location"])
    react_prompt = f"""
    {context}
    工具结果：{tool_response}
    请结合景点给出详细的旅行日程和简单的景点介绍。
    """
    response = model.invoke([HumanMessage(content=react_prompt)])
    msg = {"speaker": "AttractionExpert", "content": response.content, "timestamp": datetime.now().isoformat()}
    state["messages"].append(msg) # 添加自己的短期记忆
    print(f"\n---\n🧠🧠**AttractionExpert:**\n{response.content}")

    return {"state": state, "next": "WeatherExpert"}

def weather_node(state: AgentState) -> Dict:
    context = agents["WeatherExpert"].get_context(state)
    tool_response = tools["weather"].invoke(state["user_preferences"]["location"])
    react_prompt = f"""
{context}
工具结果：{tool_response}
请结合天气情况给出建议。
"""
    response = model.invoke([HumanMessage(content=react_prompt)])
    msg = {"speaker": "WeatherExpert", "content": response.content, "timestamp": datetime.now().isoformat()}
    state["messages"].append(msg) # 添加自己的短期记忆
    print(f"\n---\n**🧠🧠WeatherExpert:**\n{response.content}")

    return {"state": state, "next": "RestaurantExpert"}

def restaurant_node(state: AgentState) -> Dict:
    context = agents["RestaurantExpert"].get_context(state)
    tool_response = tools["restaurants"].invoke(state["user_preferences"]["location"])
    react_prompt = f"""
{context}
工具结果：{tool_response}
请推荐具体美食。
"""
    response = model.invoke([HumanMessage(content=react_prompt)])
    msg = {"speaker": "RestaurantExpert", "content": response.content, "timestamp": datetime.now().isoformat()}
    state["messages"].append(msg) # 添加自己的短期记忆
    print(f"\n---\n**🧠🧠RestaurantExpert:**\n{response.content}")

    return {"state": state, "next": "HotelExpert"}

def hotel_node(state: AgentState) -> Dict:
    context = agents["HotelExpert"].get_context(state)
    tool_response = tools["hotels"].invoke(state["user_preferences"]["location"])
    react_prompt = f"""
{context}
工具结果：{tool_response}
请推荐合适住宿。
"""
    response = model.invoke([HumanMessage(content=react_prompt)])
    msg = {"speaker": "HotelExpert", "content": response.content, "timestamp": datetime.now().isoformat()}
    state["messages"].append(msg) # 添加自己的短期记忆
    print(f"\n---\n**🧠🧠HotelExpert:**\n{response.content}")

    return {"state": state, "next": "TransportExpert"}

def transport_node(state: AgentState) -> Dict:
    context = agents["TransportExpert"].get_context(state)
    tool_response = tools["transport"].invoke(state["user_preferences"]["location"])
    react_prompt = f"""
{context}
工具结果：{tool_response}
请推荐交通方案。
"""
    response = model.invoke([HumanMessage(content=react_prompt)])
    msg = {"speaker": "TransportExpert", "content": response.content, "timestamp": datetime.now().isoformat()}
    state["messages"].append(msg) # 添加自己的短期记忆
    print(f"\n---\n**🧠🧠TransportExpert:**\n{response.content}")

    return {"state": state, "next": "BudgetExpert"}

def budget_node(state: AgentState) -> Dict:
    context = agents["BudgetExpert"].get_context(state)
    tool_response = tools["budget"].invoke({
        "days": state["user_preferences"]["days"],
        "people": state["user_preferences"]["people"]
    })
    react_prompt = f"""
{context}
工具结果：{tool_response}
请总结预算。
"""
    response = model.invoke([HumanMessage(content=react_prompt)])
    msg = {"speaker": "BudgetExpert", "content": response.content, "timestamp": datetime.now().isoformat()}
    state["messages"].append(msg) # 添加自己的短期记忆
    print(f"\n---\n**🧠🧠BudgetExpert:**\n{response.content}")

    return {"state": state, "next": "TourGuide"}

# ========================
# 构建流程图
# ========================
def should_continue(state: AgentState):
    global ROUND
    if ROUND >= state["max_rounds"]:  # 循环3次后终止
        return "exit"
    else:
        return "continue"
def build_tour_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("TourGuide", guide_node)
    workflow.add_node("AttractionExpert", attraction_node)
    workflow.add_node("WeatherExpert", weather_node)
    workflow.add_node("RestaurantExpert", restaurant_node)
    workflow.add_node("HotelExpert", hotel_node)
    workflow.add_node("TransportExpert", transport_node)
    workflow.add_node("BudgetExpert", budget_node)

    workflow.add_conditional_edges(
        "TourGuide",
        should_continue,  # 调用条件函数
        {
            "continue": "AttractionExpert",  # 返回 "continue" 则跳回 process 节点
            "exit": END  # 返回 "exit" 则终止
        }
    )
    workflow.add_edge("AttractionExpert", "WeatherExpert")
    workflow.add_edge("WeatherExpert", "RestaurantExpert")
    workflow.add_edge("RestaurantExpert", "HotelExpert")
    workflow.add_edge("HotelExpert", "TransportExpert")
    workflow.add_edge("TransportExpert", "BudgetExpert")
    workflow.add_edge("BudgetExpert", "TourGuide")

    workflow.set_entry_point("TourGuide")

    # 画图
    graph = workflow.compile()
    # png_data = graph.get_graph().draw_mermaid_png()
    # with open("workflow_diagram.png", "wb") as f:
    #     f.write(png_data)

    return graph
# ========================
# 主程序入口
# ========================

def main():
    graph = build_tour_graph()

    initial_state = AgentState(
        messages=[{
            "speaker": "System",
            "content": "欢迎使用旅游规划助手！请告诉我您的旅行地点、天数和人数。",
            "timestamp": datetime.now().isoformat()
        }],
        user_preferences={
            "location": "杭州",
            "days": 3,
            "people": 2
        },
        user_suggestions=[],
        current_speaker="TourGuide",
        max_rounds=3,
        finished=False
    )

    # 运行图
    print("\n=== 开始旅行规划 ===\n")
    final_state = graph.invoke(initial_state)

    print("\n===✅ 流程已完成! ===")
    # for msg in final_state["messages"]:
    #     print(f"{msg['speaker']}: {msg['content']}")

if __name__ == "__main__":
    main()