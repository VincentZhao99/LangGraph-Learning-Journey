import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# 导入你之前定义的本地工具
from core.tools import multiply, get_current_time

load_dotenv()

# --- 1. 配置工具箱 ---
# k=3 表示每次搜索返回最相关的 3 个网页结果
search_tool = TavilySearchResults(k=3)
tools = [multiply, get_current_time, search_tool]

# --- 2. 初始化模型与记忆 ---
model = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
)
memory = MemorySaver()

# --- 3. 注入系统指令 (Persona) ---
SYSTEM_MODIFIER = """
你是一个全能的AI助手，具备联网搜索和本地计算能力。
1. 当用户询问实时新闻、天气、政策或你需要更新知识库时，请务必使用 'tavily_search_results_json'。
2. 给出搜索结果时，请标注信息来源。
3. 结合 'get_current_time' 来为用户提供具有时效性的建议。
"""

# --- 4. 创建 Agent ---
# 我们依然保留中断机制，但你可以根据需要选择是否跳过某些工具
app = create_react_agent(
    model,
    tools=tools,
    checkpointer=memory,
    messages_modifier=SYSTEM_MODIFIER,
    interrupt_before=["tools"]
)

config = {"configurable": {"thread_id": "vincents_web_explorer_001"}}

print("🌐 联网 Agent 已上线！您可以询问任何实时问题，例如：'今天DeepSeek有什么新闻？'")

# --- 5. 动态交互主循环 ---
while True:
    user_query = input("\n👤 你的指令: ")
    if user_query.lower() in ['exit', 'q', 'quit']:
        print("再见！")
        break

    inputs = {"messages": [("user", user_query)]}

    while True:
        # 运行直到【中断】或【任务结束】
        for event in app.stream(inputs, config):
            if "agent" in event:
                msg = event["agent"]["messages"][-1]
                if msg.content:
                    print(f"🤖 AI: {msg.content}")
                if msg.tool_calls:
                    print(f"👉 AI 申请调用工具: {[t['name'] for t in msg.tool_calls]}")
                    for tc in msg.tool_calls:
                        print(f"   参数: {tc['args']}")

        state = app.get_state(config)

        if not state.next:
            break

        # --- 人机协作审批流 ---
        approval = input("⚠️ 是否批准执行上述工具? (y=批准 / n=拒绝原因 / skip=跳过并直接回答): ")

        if approval.lower() == 'y':
            inputs = None
            print("🚀 批准通过，正在执行工具...")
        elif approval.lower() == 'skip':
            # 特殊逻辑：不运行工具，强制让 AI 直接根据现有知识回答
            app.update_state(
                config,
                {"messages": [
                    ToolMessage(
                        content="用户要求跳过工具执行，请直接根据现有信息回答或告知无法回答。",
                        tool_call_id=state.values['messages'][-1].tool_calls[0]['id'])]},
                as_node="tools"
            )
            inputs = None
        else:
            # 拒绝并提供反馈
            last_msg = state.values["messages"][-1]
            for tool_call in last_msg.tool_calls:
                app.update_state(
                    config,
                    {"messages": [
                        ToolMessage(
                            content=f"操作被拒绝：{approval}",
                            tool_call_id=tool_call["id"])]},
                    as_node="tools"
                )
            inputs = {"messages": [("user", f"我不批准刚才的操作，原因是：{approval}。请重新处理。")]}