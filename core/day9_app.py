import streamlit as st
import sqlite3
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from datetime import datetime

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
    import os
    # 1. 获取当前脚本 (day9_app.py) 所在的 core 目录
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    # 2. 向上一级跳到项目根目录 (MyNotebookLM)
    PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
    # 3. 锁定 data 文件夹路径，并确保它存在
    data_dir = os.path.join(PROJECT_ROOT, "data")
    os.makedirs(data_dir, exist_ok=True)

    # 4. 拼接出我们要保存记忆的数据库路径
    db_path = os.path.join(data_dir, "checkpoints.sqlite")

    # 连接到本地 SQLite 数据库文件 (如果没有会自动创建)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)

    model = ChatOpenAI(
        model='deepseek-chat',
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
    )

    tools = [multiply, get_current_time, web_search_tool, query_knowledge_base]

    # 引导 Prompt
    current_date = datetime.now().strftime("%Y年%m月%d日")
    SYSTEM_PROMPT = f"""你是一个超级 AI 助手。请时刻记住，今天是 {current_date}。

        【你的行为守则】：
        1. 内部知识：如果用户问到公司规定或特定文档内容，请优先使用 query_knowledge_base。
        2. 实时信息：只要用户问到“新闻”、“最近”、“今天”或任何具有时效性的问题，绝对不要依赖你的内置记忆，必须立刻、主动使用 web_search_tool 进行全网搜索！
        3. 你拥有永久记忆，可以结合历史对话回答问题。"""

    # 注意：在 Web UI 中做人机交互审批比较复杂，我们今天先去掉 interrupt_before，让它全自动运行
    app = create_react_agent(model, tools=tools, checkpointer=memory, prompt=SYSTEM_PROMPT)
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
                    # 💡 修复：独立检查它是不是调了工具
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_names = [t["name"] for t in msg.tool_calls]
                        st.toast(f"🛠️ Agent 正在使用工具: {', '.join(tool_names)}", icon="🔍")

                    # 💡 修复：独立收集它的文字回复
                    if msg.content:
                        response_content = msg.content

            # 显示最终回复
            st.markdown(response_content)
            # 把回复保存到网页气泡历史中
            st.session_state.messages.append({"role": "assistant", "content": response_content})