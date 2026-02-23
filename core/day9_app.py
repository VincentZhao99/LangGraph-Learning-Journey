import streamlit as st
import sqlite3
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver

# 导入你的工具箱
from core.tools import multiply, get_current_time, web_search_tool
from core.rag_tool import query_knowledge_base

load_dotenv()

# ==========================================
# 1. 页面基本设置
# ==========================================
st.set_page_config(page_title="全能 Agent", page_icon="🤖", layout="centered")
st.title("🤖 我的全能 AI 助手")
st.markdown("集成 **本地知识库 (RAG)** + **全网搜索** + **永久记忆**")


# ==========================================
# 2. 初始化 Agent 与 SQLite 记忆 (单例模式)
# ==========================================
@st.cache_resource
def init_agent():
    # 连接到本地 SQLite 数据库文件 (如果没有会自动创建)
    conn = sqlite3.connect("data/checkpoints.sqlite", check_same_thread=False)
    memory = SqliteSaver(conn)

    model = ChatOpenAI(
        model='deepseek-chat',
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
    )

    tools = [multiply, get_current_time, web_search_tool, query_knowledge_base]

    # 引导 Prompt
    SYSTEM_PROMPT = """你是一个超级 AI 助手。
    如果问到公司规定或内部文档，请优先使用 query_knowledge_base。
    如果问到实时新闻，请使用 web_search_tool。
    你可以记住我们之前的对话内容。"""

    # 注意：在 Web UI 中做人机交互审批比较复杂，我们今天先去掉 interrupt_before，让它全自动运行
    app = create_react_agent(model, tools=tools, checkpointer=memory, messages_modifier=SYSTEM_PROMPT)
    return app


app = init_agent()

# 固定一个 Thread ID，这样刷新网页也不会失忆
config = {"configurable": {"thread_id": "vincent_web_001"}}

# ==========================================
# 3. Streamlit 聊天界面逻辑
# ==========================================
# 用 st.session_state 来保存网页上的聊天气泡
if "messages" not in st.session_state:
    st.session_state.messages = []

# 渲染历史聊天气泡
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 接收用户输入
if user_query := st.chat_input("你想查点什么？或者和我聊聊..."):
    # 1. 把用户的问题显示在网页上
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # 2. 调用 Agent 进行思考和回复
    with st.chat_message("assistant"):
        # 加一个好看的加载动画
        with st.spinner("Agent 正在大脑中疯狂运转..."):
            inputs = {"messages": [("user", user_query)]}

            # 运行 Agent 并获取最终状态
            response_content = ""
            for event in app.stream(inputs, config):
                if "agent" in event:
                    # 获取 Agent 的最新消息
                    msg = event["agent"]["messages"][-1]
                    if msg.content:
                        response_content = msg.content
                    elif msg.tool_calls:
                        # 如果是在调用工具，我们在界面上给个提示
                        tool_names = [t["name"] for t in msg.tool_calls]
                        st.toast(f"🛠️ 正在使用工具: {', '.join(tool_names)}")

            # 显示最终回复
            st.markdown(response_content)
            # 把回复保存到网页气泡历史中
            st.session_state.messages.append({"role": "assistant", "content": response_content})