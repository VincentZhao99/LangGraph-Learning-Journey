import streamlit as st
import os
import warnings
import logging  # 💡 加回日志模块
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import create_react_agent
import requests

from core.tools import web_search_tool
from core.code_tool import execute_python_code

warnings.filterwarnings("ignore")
load_dotenv()

# ==========================================
# 💡 恢复上帝视角：配置日志监控系统
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
# 2. 实例化三位员工
# ==========================================

# --- 员工 1：研究员 ---
researcher_agent = create_react_agent(
    model,
    tools=[web_search_tool, execute_python_code],
    prompt="""你是一个顶级的全栈数据研究员。
    你的任务是为爆款文章搜集最硬核的数据支撑。
    1. 你可以使用网页搜索工具查找最新资讯。
    2. 如果你需要分析本地文件（如 Excel），请务必使用 execute_python_code 工具！
    【⚠️ 核心要求】：
    你自己用工具处理完数据后，必须总结出核心数据结论（大白话），绝不能把原始的 Python 代码或者报错信息扔给撰稿人！
    """
)


def researcher_node(state: MessagesState):
    result = researcher_agent.invoke({"messages": state["messages"]})

    # 💡 核心抢修：扒开研究员的脑子，把代码写进日志！
    for msg in result["messages"]:
        # 如果大模型发出了调用工具的指令
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc['name'] == 'execute_python_code':
                    logging.info(f"💻 AI 编写的 Python 代码:\n{tc['args'].get('code', '')}")
        # 如果工具返回了执行结果
        elif hasattr(msg, 'name') and msg.name == 'execute_python_code':
            logging.info(f"✅ Python 执行结果:\n{msg.content}")

    return {"messages": [result["messages"][-1]]}


# --- 员工 2：撰稿人 ---
def writer_node(state: MessagesState):
    last_msg = state["messages"][-1].content
    if "【打回】" in last_msg:
        instruction = "你刚刚交上去的稿件被主编【打回】了！请务必在文章的最开头向主编郑重道歉，并严格根据主编的意见重写！"
    else:
        instruction = "请根据前面搜集到的真实资料，写出一篇高质量的初稿。"

    sys_msg = SystemMessage(content=f"""你是一个金牌自媒体写手。
    {instruction}
    要求：标题必须震惊，多用emoji，排版有呼吸感，语言极具煽动性！
    """)

    response = model.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}


# --- 员工 3：主编 (审核质检员) ---
def editor_node(state: MessagesState):
    # 💡 核心抢修：给主编加上“防死循环”的思想钢印！
    sys_msg = SystemMessage(content="""你是一个自媒体主编。你要审核写手交来的文章。
    如果文章有具体数据、足够吸引人，请在回复的最开头写【通过】，并给出表扬。
    如果文章平庸或缺少数据，请在开头写【打回】。
    【⚠️ 防死循环警告】：如果你看到写手已经在文章开头向你道歉并修改了，说明这是重写稿。此时只要文章里包含具体数据，请你大抬贵手，务必在开头写【通过】，绝不允许无限循环打回！""")

    response = model.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}


# ==========================================
# 3. 定义条件路由 (裁判)
# ==========================================
def route_editor(state: MessagesState):
    last_msg = state["messages"][-1].content
    if "【通过】" in last_msg:
        return END
    else:
        return "writer"

    # ==========================================


# 4. 组装复杂的循环流水线
# ==========================================
@st.cache_resource
def build_agency():
    builder = StateGraph(MessagesState)
    builder.add_node("researcher", researcher_node)
    builder.add_node("writer", writer_node)
    builder.add_node("editor", editor_node)

    builder.add_edge(START, "researcher")
    builder.add_edge("researcher", "writer")
    builder.add_edge("writer", "editor")
    builder.add_conditional_edges("editor", route_editor)

    return builder.compile()


app = build_agency()

# ==========================================
# 5. Streamlit 可视化网页
# ==========================================
st.set_page_config(page_title="AI 传媒公司", page_icon="🏭")
st.title("🏭 我的全自动 AI 传媒公司 (带审计日志版)")
st.markdown("工作流：**搜集员 (查网/写代码) ➡️ 撰稿人 (写稿) 🔁 主编 (审核把关)**")

topic = st.text_input("你想让 AI 团队写什么主题的爆款文章？",
                      value="主编，帮我写一篇关于 2026 年 2 月羽毛球馆运营数据的分析文章。让研究员先用 Python 读取 ~/Downloads/Badminton.xlsx 获取上课日志。")

if st.button("🚀 下达任务，开始干活！"):
    # 💡 把安全阀稍微调高一点，防止主编偶尔发神经
    config = {"recursion_limit": 20}
    inputs = {"messages": [HumanMessage(content=topic)]}
    final_article = ""

    with st.status("团队正在疯狂运转中...", expanded=True) as status:
        for output in app.stream(inputs, config):
            for node_name, state_update in output.items():
                msg = state_update["messages"][-1].content

                if node_name == "researcher":
                    st.write("🕵️‍♂️ **[研究员]** 资料搜集与数据分析完毕！(代码已悄悄写入 `agent_run.log`)")
                    with st.expander("查看交付给写手的数据结果"):
                        st.write(msg)

                elif node_name == "writer":
                    st.write("✍️ **[撰稿人]** 稿件已完成！战战兢兢地交由主编审核...")
                    final_article = msg
                    with st.expander("查看当前提交的草稿"):
                        st.write(msg)

                elif node_name == "editor":
                    if "【通过】" in msg:
                        st.success(f"🤬 **[主编]**：{msg}")
                    else:
                        st.error(f"🤬 **[主编]**：{msg}")
                        st.warning("🔄 触发重写机制！稿件已打回给撰稿人...")

        status.update(label="任务完成！文章已过审！", state="complete", expanded=False)
        st.balloons()

        st.write("正在尝试呼叫企业微信...")
        wx_result = publish_to_wechat(final_article)

        if wx_result.get("errcode") == 0:
            st.success("✅ 爆款文章已成功轰炸企业微信群！")
        else:
            st.error(f"❌ 企微发送失败，报错信息：{wx_result}")

    st.divider()
    st.header("📰 正式发布文章")
    st.markdown(final_article)