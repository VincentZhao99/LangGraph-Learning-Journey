# 文件路径：day13_ui_agent.py
import streamlit as st
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import logging

# 引入我们昨天打造的核武器
from core.code_tool import execute_python_code

load_dotenv()
os.makedirs("core/downloads", exist_ok=True)  # 确保沙盒文件夹存在

# ==========================================
# 1. 组装 AI 大脑 (直接写在页面顶部)
# ==========================================
model = ChatOpenAI(model='deepseek-chat', openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
                   openai_api_base=os.getenv("DEEPSEEK_BASE_URL"))
tools = [execute_python_code]
SYSTEM_PROMPT = """你是一个顶级的全能 AI 数据分析师。
如果任务涉及到数据分析，请务必使用 execute_python_code 编写 Python 代码处理本地文件。
【警告】：分析数据时只能用 df.head() 或 df.info() 查看结构，绝对不要打印全表数据！
"""
agent = create_react_agent(model, tools, prompt=SYSTEM_PROMPT)

# ==========================================
# 2. 构建 Streamlit 网页
# ==========================================
st.set_page_config(page_title="全能 AI 数据分析师", page_icon="📊", layout="wide")
st.title("📊 全能 AI 数据分析师 (Code Interpreter)")
st.markdown("上传你的 Excel/CSV，直接用大白话让我分析、画图！")

# 💡 核心武器：文件上传控件
uploaded_file = st.file_uploader("📂 请把要分析的表格拖拽到这里", type=['csv', 'xlsx', 'xls'])

if uploaded_file is not None:
    # 【大白话】：Streamlit 的上传文件是在内存里的，Agent 的代码读不到。
    # 所以我们需要先把它真实地保存到咱们的 downloads 文件夹里！
    save_path = os.path.join("core", "downloads", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"✅ 文件已成功上传并保存至沙盒：`{save_path}`")

    # 开始聊天交互
    user_query = st.text_input("👤 你想让我怎么分析这份数据？",
                               placeholder="例如：帮我读取这个文件，告诉我销量前三的城市，并画一张柱状图保存下来。")

    if st.button("🚀 开始分析"):
        with st.chat_message("user"):
            st.write(user_query)

        with st.chat_message("assistant"):
            with st.status("🧠 AI 正在疯狂写代码分析中...", expanded=True) as status:
                inputs = {"messages": [("user", f"文件路径是：{save_path}。{user_query}")]}

                # 实时打印 Agent 的操作过程
                for event in agent.stream(inputs):
                    if "agent" in event and event["agent"]["messages"][-1].tool_calls:
                        st.write("🛠️ 正在编写并执行 Python 代码...")
                    elif "tools" in event:
                        st.write("✅ 代码执行完毕，获取到运算结果。")

                # 获取最终结论
                final_reply = event["agent"]["messages"][-1].content if "agent" in event else ""
                status.update(label="分析完成！", state="complete", expanded=False)

            st.markdown(final_reply)
            st.balloons()