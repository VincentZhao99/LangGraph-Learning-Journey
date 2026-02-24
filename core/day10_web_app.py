import streamlit as st
import os
import warnings
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import create_react_agent

# 屏蔽烦人的版本警告
warnings.filterwarnings("ignore")
load_dotenv()

# 导入联网搜索工具
from core.tools import web_search_tool

# ==========================================
# 1. 初始化模型
# ==========================================
model = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
)

# ==========================================
# 2. 实例化三位员工 (定义节点)
# ==========================================
# --- 员工 1：研究员 ---
researcher_agent = create_react_agent(
    model,
    tools=[web_search_tool],
    prompt="你是一个严谨的资料搜集员。请使用搜索工具查阅最新信息，并总结出核心事实和数据。绝不能瞎编！"
)


def researcher_node(state: MessagesState):
    result = researcher_agent.invoke(state)
    return {"messages": [result["messages"][-1]]}


# --- 员工 2：撰稿人 ---
def writer_node(state: MessagesState):
    sys_msg = SystemMessage(content="""你是一个金牌自媒体写手。请根据历史信息写一篇短文。
    注意：如果看到了主编的【打回】意见，请务必向主编道歉，并根据他的严厉意见重写！
    要求：标题必须震惊，多用emoji，排版有呼吸感。""")
    response = model.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}


# --- 员工 3：主编 (新加入！) ---
def editor_node(state: MessagesState):
    sys_msg = SystemMessage(content="""你是一个极其苛刻的自媒体主编。你要审核写手刚刚交来的文章。
    如果文章有具体数据、足够吸引人、emoji 运用得当，请在回复的最开头写【通过】，并给出简单表扬。
    如果文章平庸、缺少真实数据或不够震惊，请在回复的最开头写【打回】，并给出极其严厉的修改意见！""")
    response = model.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}


# ==========================================
# 3. 定义主编的“裁判”逻辑 (条件路由)
# ==========================================
def route_editor(state: MessagesState):
    # 获取流水线里最新的一句话（主编刚刚说的话）
    last_msg = state["messages"][-1].content
    if "【通过】" in last_msg:
        return END  # 审核通过，文章发布！
    else:
        return "writer"  # 审核失败，把箭头指回写手，让他重写！


# ==========================================
# 4. 组装复杂的循环流水线
# ==========================================
@st.cache_resource
def build_agency():
    builder = StateGraph(MessagesState)

    # 录入三个员工
    builder.add_node("researcher", researcher_node)
    builder.add_node("writer", writer_node)
    builder.add_node("editor", editor_node)

    # 画流程连线
    builder.add_edge(START, "researcher")  # 老板发话 -> 研究员去搜集
    builder.add_edge("researcher", "writer")  # 搜集完 -> 给写手写初稿
    builder.add_edge("writer", "editor")  # 写手写完 -> 给主编审核

    # 💡 灵魂一步：主编审核后，根据 route_editor 的判断，决定去 END 还是回到 writer
    builder.add_conditional_edges("editor", route_editor)

    return builder.compile()


app = build_agency()

# ==========================================
# 5. Streamlit 可视化网页
# ==========================================
st.set_page_config(page_title="AI 传媒公司", page_icon="🏭")
st.title("🏭 我的全自动 AI 传媒公司")
st.markdown("工作流：**搜集员 (查资料) ➡️ 撰稿人 (写稿) 🔁 主编 (审核把关)**")

topic = st.text_input("你想让 AI 团队写什么主题的爆款文章？", value="请查一下马斯克最近的猛料！")

if st.button("🚀 下达任务，开始干活！"):
    # 为了防止 AI 互相杠上无限死循环重写，我们给 Graph 设个强制安全阀：最多流转 15 步
    config = {"recursion_limit": 15}
    inputs = {"messages": [HumanMessage(content=topic)]}

    final_article = ""  # 临时存放过审的终稿

    with st.status("团队正在疯狂运转中...", expanded=True) as status:
        # 开始启动流水线！
        for output in app.stream(inputs, config):
            for node_name, state_update in output.items():
                msg = state_update["messages"][-1].content

                # 根据当前干活的节点，在网页上打印对应的状态
                if node_name == "researcher":
                    st.write("🕵️‍♂️ **[研究员]** 资料搜集完毕，正在移交撰稿人...")
                    with st.expander("查看原始资料"):
                        st.write(msg)

                elif node_name == "writer":
                    st.write("✍️ **[撰稿人]** 稿件已完成！战战兢兢地交由主编审核...")
                    final_article = msg  # 先把稿子存在这里，如果一会过了，这就是终稿
                    with st.expander("查看当前提交的草稿"):
                        st.write(msg)

                elif node_name == "editor":
                    if "【通过】" in msg:
                        st.success(f"🤬 **[主编]**：{msg}")
                    else:
                        st.error(f"🤬 **[主编]**：{msg}")
                        st.warning("🔄 触发重写机制！稿件已打回给撰稿人...")

        status.update(label="任务完成！文章已过审！", state="complete", expanded=False)
        st.balloons()  # 放气球庆祝！

    # 流水线彻底跑完后，把存下来的终稿正式发表在网页上
    st.divider()
    st.header("📰 正式发布文章")
    st.markdown(final_article)