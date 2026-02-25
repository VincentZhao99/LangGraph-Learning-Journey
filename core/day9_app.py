import streamlit as st
import sqlite3
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from datetime import datetime

# 导入你的工具箱 (给 Agent 配备的武器库)
from core.tools import multiply, get_current_time, web_search_tool
from core.rag_tool import query_knowledge_base

# 加载环境变量 (比如你的 DEEPSEEK_API_KEY)
load_dotenv()

# ==========================================
# 1. 页面基本设置 (搞网页装修)
# ==========================================
# 【大白话】：定义网页的标题、浏览器标签页的图标，让页面看起来居中(居中看着像手机App)
st.set_page_config(page_title="全能 Agent", page_icon="🤖", layout="centered")
st.title("🤖 我的全能 AI 助手")
st.markdown("集成 **本地知识库 (RAG)** + **全网搜索** + **永久记忆**")


# ==========================================
# 2. 初始化 Agent 与 SQLite 记忆 (核心大脑组装)
# ==========================================
# 【大白话】：@st.cache_resource 非常关键！Streamlit 每次点按钮都会重新跑一遍整个文件。
# 加了这个装饰器，就像是把 Agent 锁在保险箱里，只在第一次打开网页时组装一次，后面就不会重复创建了，省钱又省时间。
@st.cache_resource
def init_agent():
    import os

    # --- 下面这几步是为了精准找到放数据库的“地盘” ---
    # 1. 获取当前脚本 (day9_app.py) 所在的 core 目录
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    # 2. 向上一级跳到项目根目录 (MyNotebookLM)
    PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
    # 3. 锁定 data 文件夹路径，并确保它存在 (没有就建一个)
    data_dir = os.path.join(PROJECT_ROOT, "data")
    os.makedirs(data_dir, exist_ok=True)

    # 4. 拼接出我们要保存记忆的数据库路径
    db_path = os.path.join(data_dir, "checkpoints.sqlite")

    # 【大白话】：物理外挂脑！连接到本地 SQLite 数据库。刚才你做的破坏性测试就是删它。
    # 只要这个文件在，Agent 就永远不会失忆。
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)

    # 【大白话】：雇佣大模型打工人 (这里用的是 DeepSeek)
    model = ChatOpenAI(
        model='deepseek-chat',
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
    )

    # 【大白话】：把工具打包成一个列表，待会儿一股脑塞给 Agent
    tools = [multiply, get_current_time, web_search_tool, query_knowledge_base]

    # 【大白话】：Agent 的紧箍咒 / 员工手册。告诉它什么时候该用什么工具。
    current_date = datetime.now().strftime("%Y年%m月%d日")
    SYSTEM_PROMPT = f"""你是一个超级 AI 助手。请时刻记住，今天是 {current_date}。

        【你的行为守则】：
        1. 内部知识：如果用户问到公司规定或特定文档内容，请优先使用 query_knowledge_base。
        2. 实时信息：只要用户问到“新闻”、“最近”、“今天”或任何具有时效性的问题，绝对不要依赖你的内置记忆，必须立刻、主动使用 web_search_tool 进行全网搜索！
        3. 你拥有永久记忆，可以结合历史对话回答问题。"""

    # 【大白话】：LangGraph 提供的现成脚手架！直接把 大模型 + 工具 + 记忆 + 紧箍咒 丢进去，
    # 它会自动帮你画一张“ReAct 循环图”，不用你手动 add_node 和 add_edge 啦！
    app = create_react_agent(model, tools=tools, checkpointer=memory, prompt=SYSTEM_PROMPT)
    return app


# 执行初始化
app = init_agent()

# 【大白话】：记忆抽屉的钥匙！SQLite 里可以存无数个人的记忆，
# 用这个 thread_id 去开锁，就能取回对应的那份历史记录。
config = {"configurable": {"thread_id": "vincent_web_001"}}

# ==========================================
# 3. Streamlit 聊天界面逻辑 (迎宾与跑腿)
# ==========================================

# 【大白话】：这里是网页的“表面短时记忆”。
# 因为 SQLite 只负责给 Agent 看，网页自己不知道过去聊了啥，所以得用 st.session_state 把气泡存起来。
if "messages" not in st.session_state:
    st.session_state.messages = []

# 【大白话】：刷新网页时，把表面短时记忆里的气泡，一个个重新画到屏幕上
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 【大白话】：页面最底下的聊天输入框。一旦用户敲回车，这个 if 条件就成立，开始干活！
if user_query := st.chat_input("你想查点什么？或者和我聊聊..."):

    # 1. 先把用户的问题记到“表面记忆”里，并画在网页上
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # 2. 准备显示 AI 的气泡
    with st.chat_message("assistant"):
        # 加一个好看的转圈圈加载动画，安抚用户情绪
        with st.spinner("Agent 正在大脑中疯狂运转..."):
            # 把用户的话打包成 LangGraph 认识的格式
            inputs = {"messages": [("user", user_query)]}

            # 【大白话】：让图跑起来！app.stream 会源源不断吐出节点运行的状态
            response_content = ""
            for event in app.stream(inputs, config):
                # 如果这个事件是 Agent 发出的（而不是工具发出的）
                if "agent" in event:
                    msg = event["agent"]["messages"][-1]

                    # 💡 【大白话】：偷窥 Agent 的大脑！如果它决定调工具，我们就抓取工具名字
                    # 并在网页右上角弹出一个小提示 (st.toast)，让用户知道它没偷懒，在查资料。
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_names = [t["name"] for t in msg.tool_calls]
                        st.toast(f"🛠️ Agent 正在使用工具: {', '.join(tool_names)}", icon="🔍")

                    # 💡 【大白话】：捕捉 Agent 最终想对用户说的话
                    if msg.content:
                        response_content = msg.content

            # 【大白话】：流程跑完，把 Agent 憋出来的最终大招打在屏幕上
            st.markdown(response_content)

            # 【大白话】：别忘了把这句最终回复也塞进网页的“表面记忆”里，不然刷新网页就没了
            st.session_state.messages.append({"role": "assistant", "content": response_content})