import streamlit as st
import os
import warnings
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import create_react_agent
import requests

# 导入咱们打造的工具
from core.tools import web_search_tool
from core.code_tool import execute_python_code

# 屏蔽底层警告
warnings.filterwarnings("ignore")
load_dotenv()


def publish_to_wechat(article_content):
    """【防弹版】带字数限制和错误反馈的企微发送器"""
    webhook_url = os.getenv("WEBHOOK_URL")

    # 💡 微调 1：安全校验，防止没配环境变量导致崩溃
    if not webhook_url:
        return {"errcode": -1, "errmsg": "本地 .env 文件中未配置 WEBHOOK_URL"}

    # ⚠️ 强行截断！防止大模型写的文章太长撑爆企微的 4096 字节限制
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
# 1. 初始化模型 (公司统一的大脑)
# ==========================================
model = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
)

# ==========================================
# 2. 实例化三位员工 (定义打工人节点)
# ==========================================

# --- 员工 1：研究员 (真·全自动特工，Agent in Agent 架构) ---
researcher_agent = create_react_agent(
    model,
    tools=[web_search_tool, execute_python_code],  # 💡 双武器直接挂载
    prompt="""你是一个顶级的全栈数据研究员。
    你的任务是为爆款文章搜集最硬核的数据支撑。
    1. 你可以使用网页搜索工具查找最新资讯。
    2. 如果你需要计算复杂的数据、或者需要写 Python 脚本去读取某个本地文件（如 Excel），请毫不犹豫地使用 execute_python_code 工具！
    【⚠️ 极其重要的工作要求】：
    你自己用工具把数据处理完后，必须总结出关键的商业洞察和核心数据结论，用大白话输出！绝不能把原始的 Python 代码或者报错信息直接扔给撰稿人！
    """
)


def researcher_node(state: MessagesState):
    # 把历史聊天记录塞给研究员 Agent，让它去小黑屋里疯狂干活并调用工具
    result = researcher_agent.invoke({"messages": state["messages"]})
    # 提取最终结论交给下一棒
    return {"messages": [result["messages"][-1]]}


# --- 员工 2：撰稿人 (动态听令) ---
def writer_node(state: MessagesState):
    last_msg = state["messages"][-1].content

    # 精准判定是否被打回
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
    sys_msg = SystemMessage(content="""你是一个极其苛刻的自媒体主编。你要审核写手刚刚交来的文章。
    如果文章有具体数据、足够吸引人、emoji 运用得当，请在回复的最开头写【通过】，并给出简单表扬。
    如果文章平庸、缺少真实数据或不够震惊，请在回复的最开头写【打回】，并给出极其严厉的修改意见！""")

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
st.title("🏭 我的全自动 AI 传媒公司")
st.markdown("工作流：**搜集员 (查网/写代码) ➡️ 撰稿人 (写稿) 🔁 主编 (审核把关)**")

topic = st.text_input("你想让 AI 团队写什么主题的爆款文章？", value="请帮我查一下马斯克最近的猛料！")

if st.button("🚀 下达任务，开始干活！"):
    config = {"recursion_limit": 15}
    inputs = {"messages": [HumanMessage(content=topic)]}

    final_article = ""

    with st.status("团队正在疯狂运转中...", expanded=True) as status:
        for output in app.stream(inputs, config):
            for node_name, state_update in output.items():
                msg = state_update["messages"][-1].content

                if node_name == "researcher":
                    st.write("🕵️‍♂️ **[研究员]** 资料搜集与数据分析完毕，正在移交撰稿人...")
                    with st.expander("查看原始资料"):
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