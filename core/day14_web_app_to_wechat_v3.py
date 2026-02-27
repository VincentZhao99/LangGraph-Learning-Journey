import streamlit as st
import os
import warnings
import logging
import uuid
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver  # 💡 核心黑科技：短期记忆体
import requests

from core.tools import web_search_tool
from core.code_tool import execute_python_code

warnings.filterwarnings("ignore")
load_dotenv()

# ==========================================
# 💡 日志配置
# ==========================================
logging.basicConfig(
    filename='agent_run.log',
    level=logging.INFO,
    format='\n' + '=' * 40 + '\n%(asctime)s - %(levelname)s\n%(message)s',
    encoding='utf-8'
)


def publish_to_wechat(article_content):
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        return {"errcode": -1, "errmsg": "本地 .env 文件中未配置 WEBHOOK_URL"}

    if len(article_content) > 1200:
        safe_content = article_content[:1200] + "\n\n...（受限于企微字数，后文省略）"
    else:
        safe_content = article_content

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"📢 **[AI 传媒公司] 最新爆款！**\n\n{safe_content}"
        }
    }
    try:
        response = requests.post(webhook_url, json=payload)
        return response.json()
    except Exception as e:
        return {"errcode": -1, "errmsg": str(e)}


# ==========================================
# 1. 初始化模型
# ==========================================
model = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
)

# ==========================================
# 2. 实例化打工人节点
# ==========================================

# --- 员工 1：研究员 ---
researcher_agent = create_react_agent(
    model,
    tools=[web_search_tool, execute_python_code],
    prompt="""你是一个顶级的全栈数据研究员。
    你需要使用 execute_python_code 或 web_search_tool 获取硬核数据。
    你自己处理完数据后，必须用大白话总结出核心结论，绝不能直接扔出代码或报错！"""
)


def researcher_node(state: MessagesState):
    result = researcher_agent.invoke({"messages": state["messages"]})
    for msg in result["messages"]:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc['name'] == 'execute_python_code':
                    logging.info(f"💻 AI Python代码:\n{tc['args'].get('code', '')}")
        elif hasattr(msg, 'name') and msg.name == 'execute_python_code':
            logging.info(f"✅ Python结果:\n{msg.content}")
    return {"messages": [result["messages"][-1]]}


# --- 员工 2：撰稿人 ---
def writer_node(state: MessagesState):
    last_msg = state["messages"][-1].content

    # 💡 根据挨骂的对象不同，动态改变态度！
    if "【老板打回】" in last_msg:
        instruction = "⚠️ 最高危机！老板亲自把你的稿件打回了！请务必在文章最开头向老板滑跪道歉，并严格根据老板的意见重写！"
    elif "【打回】" in last_msg:
        instruction = "你的稿件被主编【打回】了！请在文章的最开头向主编道歉，并根据意见重写！"
    else:
        instruction = "请根据前面搜集到的真实资料，写出一篇高质量的初稿。"

    sys_msg = SystemMessage(content=f"""你是一个金牌自媒体写手。
    {instruction}
    要求：标题必须震惊，多用emoji，排版有呼吸感，语言极具煽动性！
    """)

    response = model.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}


# --- 员工 3：主编 ---
def editor_node(state: MessagesState):
    sys_msg = SystemMessage(content="""你要审核写手交来的文章。
    如果文章有具体数据、足够吸引人，开头写【通过】，并表扬。
    平庸或缺数据，开头写【打回】。
    【⚠️ 防死循环警告】：若写手已道歉并修改，且含具体数据，请务必写【通过】，绝不允许无限循环！""")
    response = model.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}


# --- 💡 新增员工 4：发报房 (专门负责推企微) ---
def publisher_node(state: MessagesState):
    # 巧妙提取：倒数第 2 条消息一定是写手的最终稿（倒数第 1 条是主编的表扬）
    final_article = state["messages"][-2].content
    wx_result = publish_to_wechat(final_article)

    if wx_result.get("errcode") == 0:
        return {"messages": [SystemMessage(content="爆款文章已成功轰炸企业微信群！")]}
    else:
        return {"messages": [SystemMessage(content=f"企微发送失败，报错：{wx_result}")]}


# ==========================================
# 3. 裁判路由
# ==========================================
def route_editor(state: MessagesState):
    last_msg = state["messages"][-1].content
    if "【通过】" in last_msg:
        return "publisher"  # 💡 主编过审后，不是下班，而是送去发报房
    else:
        return "writer"

    # ==========================================


# 4. 组装复杂的循环流水线 (带断点版)
# ==========================================
@st.cache_resource
def build_agency():
    builder = StateGraph(MessagesState)
    builder.add_node("researcher", researcher_node)
    builder.add_node("writer", writer_node)
    builder.add_node("editor", editor_node)
    builder.add_node("publisher", publisher_node)  # 注册发报房

    builder.add_edge(START, "researcher")
    builder.add_edge("researcher", "writer")
    builder.add_edge("writer", "editor")
    builder.add_conditional_edges("editor", route_editor)
    builder.add_edge("publisher", END)

    # 💡 核心黑科技：装上记忆体，并且在 publisher 节点前强行拉手刹！
    memory = MemorySaver()
    return builder.compile(checkpointer=memory, interrupt_before=["publisher"])


app = build_agency()

# ==========================================
# 5. Streamlit 可视化网页 (老板审批工作台)
# ==========================================
st.set_page_config(page_title="AI 传媒公司", page_icon="🏭")
st.title("🏭 全自动 AI 传媒公司 (HITL 老板签字版)")

# 💡 给每个任务分配一个唯一档案号 (Thread ID)，这样记忆体才知道存取哪个档案
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

config = {"configurable": {"thread_id": st.session_state.thread_id}, "recursion_limit": 20}

topic = st.text_input("你想让 AI 团队写什么主题的文章？",
                      value="主编，帮我写一篇 2026 年 2 月羽毛球馆数据分析。让研究员先用 Python 读取 ~/Downloads/Badminton.xlsx")


# 定义统一的运行流转引擎
def run_graph(inputs=None):
    with st.status("团队疯狂运转中...", expanded=True) as status:
        for output in app.stream(inputs, config):
            for node_name, state_update in output.items():
                msg = state_update["messages"][-1].content
                if node_name == "researcher":
                    st.write("🕵️‍♂️ **[研究员]** 数据分析完毕！(代码已记入日志)")
                elif node_name == "writer":
                    st.write("✍️ **[撰稿人]** 稿件已完成！交由主编审核...")
                    st.session_state.draft = msg  # 偷偷存一份草稿给老板看
                elif node_name == "editor":
                    if "【通过】" in msg:
                        st.success(f"🤬 **[主编]**：{msg}")
                    else:
                        st.error(f"🤬 **[主编]**：{msg}")
                elif node_name == "publisher":
                    st.info(f"🚀 **[发报房]**：{msg}")

        # 💡 运行停下后，偷看一眼程序的“下一步”打算干嘛？
        current_state = app.get_state(config)
        if current_state.next and "publisher" in current_state.next:
            # 如果它下一步想进发报房，说明被咱们的断点拦住了！
            status.update(label="✋ 触发拦截！等待老板最终审批！", state="error", expanded=True)
            st.session_state.awaiting_approval = True
        else:
            status.update(label="✅ 任务彻底完成！", state="complete", expanded=False)
            st.session_state.awaiting_approval = False


if st.button("🚀 下达任务，开始干活！"):
    # 每次点新任务，换一个新档案号，清空老板审批台
    st.session_state.thread_id = str(uuid.uuid4())
    config["configurable"]["thread_id"] = st.session_state.thread_id
    st.session_state.awaiting_approval = False

    run_graph({"messages": [HumanMessage(content=topic)]})

# ==========================================
# 💡 老板专属特权：最高审批台！
# ==========================================
if st.session_state.get("awaiting_approval", False):
    st.divider()
    st.header("🚨 老板最终审批台")
    st.warning("⚠️ 系统已物理挂起！主编已审核通过，等待您签字确认后才会推送到企业微信。")

    st.markdown("### 📝 待发布稿件预览：")
    st.info(st.session_state.get("draft", "未找到草稿..."))

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("✅ 朕看过了，批准发布！", type="primary", use_container_width=True):
            st.success("老板已签字，正在执行发布指令...")
            run_graph(None)  # None 表示解除冻结，顺着往下跑（进发报房）
            st.balloons()
            st.rerun()  # 刷新网页，关掉审批台

    with col2:
        reject_reason = st.text_input("如果不满意，请输入打回意见：", placeholder="例如：标题不够响亮，重写！")
        if st.button("❌ 狠狠打回重写", use_container_width=True):
            if not reject_reason:
                st.error("请先填写打回原因！")
            else:
                # 💡 黑客级操作：直接篡改系统的运行历史，假装是“老板”发话了！
                app.update_state(
                    config,
                    {"messages": [HumanMessage(content=f"【老板打回】老板看了不满意，说：{reject_reason}")]},
                    as_node="editor"  # 狸猫换太子：挂载在主编节点名下，触发重写路由！
                )
                st.error("已下达最高指令，撰稿人正在重写...")
                run_graph(None)  # 解冻系统，它会顺着“打回”的逻辑回去找写手！