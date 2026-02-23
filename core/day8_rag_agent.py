import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import ToolMessage

# 导入你之前定义的所有工具
from core.tools import multiply, get_current_time, web_search_tool
from core.rag_tool import query_knowledge_base  # 👈 这是你刚刚建的 RAG 工具

load_dotenv()

# --- 1. 配置模型 ---
# 建议使用 deepseek-chat，它在处理 RAG 返回的长上下文时性价比极高
model = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
)

# --- 2. 内存与工具箱 ---
memory = MemorySaver()
tools = [multiply, get_current_time, web_search_tool, query_knowledge_base]

# --- 3. 核心指令：引导 Agent 区分“联网”与“私有文档” ---
SYSTEM_MODIFIER = """你是一个全能型 Agent。
你现在拥有访问用户私有文档的能力（通过 query_knowledge_base 工具）。

策略指引：
1. 如果用户询问关于其个人文件、特定报告、内部规章的内容，请【首选】使用 query_knowledge_base。
2. 如果用户询问实时新闻或公开知识，请使用 tavily_search_results_json。
3. 如果文档中找不到答案，请诚实告知，不要编造，并询问是否需要联网搜索。
"""

# --- 4. 构建 Agent ---
# 建议继续开启 interrupt_before，因为 RAG 检索也需要消耗 Embedding 和 LLM Token
app = create_react_agent(
    model,
    tools=tools,
    checkpointer=memory,
    messages_modifier=SYSTEM_MODIFIER,
    interrupt_before=["tools"]
)

config = {"configurable": {"thread_id": "vincents_rag_session_001"}}

print("📚 Day 8 RAG Agent 已上线！")
print("你可以问我关于 data/ 文件夹下 PDF 的内容了。")

# --- 5. 交互循环 ---
while True:
    user_query = input("\n👤 你的指令: ")
    if user_query.lower() in ['exit', 'q', 'quit']:
        break

    inputs = {"messages": [("user", user_query)]}

    while True:
        for event in app.stream(inputs, config):
            if "agent" in event:
                msg = event["agent"]["messages"][-1]
                if msg.content:
                    print(f"🤖 AI: {msg.content}")
                if msg.tool_calls:
                    print(f"👉 AI 准备查阅资料: {[t['name'] for t in msg.tool_calls]}")

        state = app.get_state(config)
        if not state.next:
            break

        # 审批流
        approval = input("⚠️ 是否允许 Agent 执行该检索操作? (y/n): ")
        if approval.lower() == 'y':
            inputs = None
        else:
            # 拒绝逻辑
            last_msg = state.values["messages"][-1]
            for tool_call in last_msg.tool_calls:
                app.update_state(
                    config,
                    {"messages": [ToolMessage(content=f"用户拒绝了该操作。", tool_call_id=tool_call["id"])]},
                    as_node="tools"
                )
            inputs = {"messages": [("user", "我不允许你查看那个文档，请尝试用其他方式回答。")]}