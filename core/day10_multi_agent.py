import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import create_react_agent

# 导入你的联网搜索工具
from core.tools import web_search_tool

load_dotenv()

print("🚀 正在组装 AI 流水线...")

# ==========================================
# 1. 准备基础资源：大模型和工具
# ==========================================
model = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
)

# ==========================================
# 2. 实例化一号员工：研究员 (Researcher)
# ==========================================
# 研究员配有 web_search_tool，负责全网找资料
researcher_prompt = "你是一个严谨的资料搜集员。请使用搜索工具查阅最新信息，并总结出核心事实和数据。不要瞎编！"
researcher_agent = create_react_agent(model, tools=[web_search_tool], state_modifier=researcher_prompt)


def researcher_node(state: MessagesState):
    print("🕵️‍♂️ [研究员] 正在全网疯狂搜索资料...")
    # 把当前的状态（聊天记录）传给研究员，让他去干活
    result = researcher_agent.invoke(state)
    # 研究员干完活后，提取他说的最后一段话，存入流水线状态中
    return {"messages": [result["messages"][-1]]}


# ==========================================
# 3. 实例化二号员工：撰稿人 (Writer)
# ==========================================
# 撰稿人没有搜索工具，他的任务是根据研究员找来的资料，写成爆款文章
def writer_node(state: MessagesState):
    print("✍️ [撰稿人] 收到资料，正在润色爆款文章...")

    # 获取流水线里所有的历史信息（包括刚才研究员查到的资料）
    messages = state["messages"]

    # 给撰稿人下达的人设指令
    sys_msg = SystemMessage(
        content="你是一个金牌自媒体爆款写手。请根据对话历史中的研究资料，写一篇吸引人的短文。要求：标题震惊，多用emoji，分段清晰，语气激动！")

    # 撰稿人直接开始写（不需要工具）
    response = model.invoke([sys_msg] + messages)
    return {"messages": [response]}


# ==========================================
# 4. 组装流水线 (画图)
# ==========================================
# 创建一张空白的图，数据结构使用内置的 MessagesState (专门用来存聊天气泡)
builder = StateGraph(MessagesState)

# 把两个员工安排进图里（添加节点）
builder.add_node("researcher", researcher_node)
builder.add_node("writer", writer_node)

# 设定流水线的走向（连线）
builder.add_edge(START, "researcher")  # 开始 -> 找研究员
builder.add_edge("researcher", "writer")  # 研究员找完资料 -> 交给撰稿人
builder.add_edge("writer", END)  # 撰稿人写完 -> 结束

# 编译生成最终的多智能体网络
multi_agent_app = builder.compile()

# ==========================================
# 5. 测试运行
# ==========================================
if __name__ == "__main__":
    # 我们给这个 AI 团队下达的主题
    topic = "请帮我查一下，最近一两个月，马斯克 (Elon Musk) 的 SpaceX 或者特斯拉有什么大新闻？"

    print(f"\n老板发话了：{topic}\n" + "=" * 50)

    # 启动流水线
    inputs = {"messages": [HumanMessage(content=topic)]}

    final_article = ""

    # 逐步打印团队的工作进度，并顺手捞出最终结果
    for output in multi_agent_app.stream(inputs):
        for node_name, state_update in output.items():
            print(f"\n✅ {node_name} 节点执行完毕！")
            # 每次节点流转，都把最新的一条消息记下来。
            # 最后一个节点(writer)写完后，这里存的自然就是最终的爆款文章！
            final_article = state_update["messages"][-1].content

    print("\n" + "=" * 50)
    print("🎉 最终成稿：\n")
    print(final_article)