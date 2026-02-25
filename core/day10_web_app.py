import streamlit as st
import os
import warnings
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import create_react_agent
import requests
import json
# 【大白话】：开发过程中有时候底层库会报一些不影响运行的警告（红字），
# 加这句能把它们静音，保证 Streamlit 网页清清爽爽。
warnings.filterwarnings("ignore")
load_dotenv()

# WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的真实KEY"

def publish_to_wechat(article_content):
    """【防弹版】带字数限制和错误反馈的企微发送器"""
    # ⚠️ 防坑核心：强行截断！防止大模型写的文章太长撑爆企微的 4096 字节限制
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
        response = requests.post(
            os.getenv("WEBHOOK_URL"),
            json=payload
        )
        # 把企微服务器的真实回答返回出去
        return response.json()
    except Exception as e:
        return {"errcode": -1, "errmsg": str(e)}

# 导入联网搜索工具
from core.tools import web_search_tool

# ==========================================
# 1. 初始化模型 (给公司配统一的大脑)
# ==========================================
# 【大白话】：全公司上下（研究员、写手、主编）共用同一个大模型底座，
# 就像公司统一采购了 DeepSeek 的大脑芯片。
model = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
)

# ==========================================
# 2. 实例化三位员工 (定义打工人节点)
# ==========================================

# --- 员工 1：研究员 ---
# 【大白话】：这是个自带工具包的高级打工人（Agent）。用 create_react_agent 给它配了上网搜索的权利。
researcher_agent = create_react_agent(
    model,
    tools=[web_search_tool],
    prompt="你是一个严谨的资料搜集员。请使用搜索工具查阅最新信息，并总结出核心事实和数据。绝不能瞎编！"
)


def researcher_node(state: MessagesState):
    # 【大白话】：让研究员干活，干完活把最新的结果（最后一条消息）塞进公司的状态总线（state）里。
    result = researcher_agent.invoke(state)
    return {"messages": [result["messages"][-1]]}

# --- 升级版员工 2：撰稿人 (动态听令) ---
def writer_node(state: MessagesState):
    # 1. 偷看一眼上一条消息是谁发的，内容是什么
    last_msg = state["messages"][-1].content

    # 2. 用 Python 代码做绝对精准的判断
    if "【打回】" in last_msg:
        # 如果上一步是被主编骂了，你就得乖乖道歉并重写！
        instruction = "你刚刚交上去的稿件被主编【打回】了！请务必在文章的最开头向主编郑重道歉，并严格根据主编的意见重写！"
    else:
        # 如果上一步是研究员查资料回来，那就正常写初稿，绝口不提道歉的事
        instruction = "请根据前面搜集到的真实资料，写出一篇高质量的初稿。"

    # 3. 动态组合最终的系统指令
    sys_msg = SystemMessage(content=f"""你是一个金牌自媒体写手。
    {instruction}
    要求：标题必须震惊，多用emoji，排版有呼吸感，语言极具煽动性！
    """)

    # 开始干活 结合历史聊天记录（包括资料和被骂的记录）开始写稿
    response = model.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}

# --- 员工 3：主编 (审核质检员) ---
def editor_node(state: MessagesState):
    # 【大白话】：全村的希望！主编的 System Prompt 极其关键。
    # 我们强行规定了它的输出格式：必须在开头写【通过】或【打回】，这决定了后面的程序怎么走。
    sys_msg = SystemMessage(content="""你是一个极其苛刻的自媒体主编。你要审核写手刚刚交来的文章。
    如果文章有具体数据、足够吸引人、emoji 运用得当，请在回复的最开头写【通过】，并给出简单表扬。
    如果文章平庸、缺少真实数据或不够震惊，请在回复的最开头写【打回】，并给出极其严厉的修改意见！""")

    response = model.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}


# ==========================================
# 3. 定义主编的“裁判”逻辑 (条件路由)
# ==========================================
def route_editor(state: MessagesState):
    # 【大白话】：这里是代码层面而不是大模型层面的判断！
    # 取出主编刚刚吐出来的最后一段话，像机器扫描一样寻找“【通过】”这三个字。
    last_msg = state["messages"][-1].content
    if "【通过】" in last_msg:
        return END  # 审核通过，流水线可以下班了！
    else:
        return "writer"  # 没找到“【通过】”（也就是被打回了），把箭头无情地指回写手节点！


# ==========================================
# 4. 组装复杂的循环流水线 (画图纸)
# ==========================================
# 【大白话】：一样用 @st.cache_resource 锁住，防止每次点按钮都重新建公司。
@st.cache_resource
def build_agency():
    builder = StateGraph(MessagesState)

    # 办理入职：把三个干活的函数注册进系统
    builder.add_node("researcher", researcher_node)
    builder.add_node("writer", writer_node)
    builder.add_node("editor", editor_node)

    # 画固定单行道：老板发话 -> 研究员 -> 写手 -> 主编
    builder.add_edge(START, "researcher")
    builder.add_edge("researcher", "writer")
    builder.add_edge("writer", "editor")

    # 💡 【大白话】：灵魂的一步！主编干完活后，系统去问 route_editor 这个裁判，
    # 裁判指哪儿（END 还是 writer），下一步就去哪儿。这就形成了“死循环重写”的机制。
    builder.add_conditional_edges("editor", route_editor)

    return builder.compile()


app = build_agency()

# ==========================================
# 5. Streamlit 可视化网页 (给老板看的驾驶舱)
# ==========================================
st.set_page_config(page_title="AI 传媒公司", page_icon="🏭")
st.title("🏭 我的全自动 AI 传媒公司")
st.markdown("工作流：**搜集员 (查资料) ➡️ 撰稿人 (写稿) 🔁 主编 (审核把关)**")

# 老板输入框
topic = st.text_input("你想让 AI 团队写什么主题的爆款文章？", value="请查一下马斯克最近的猛料！")

if st.button("🚀 下达任务，开始干活！"):
    # ⚠️ 【大白话】：保险丝！因为我们有“打回重写”的循环，如果主编太杠精，或者写手太笨，
    # 可能会无限死循环。 recursion_limit: 15 就是说，最多循环流转 15 步，强行断电，防止把 API 余额烧光！
    config = {"recursion_limit": 15}
    inputs = {"messages": [HumanMessage(content=topic)]}

    final_article = ""  # 准备个空盒子，等过审了就把文章装进来

    # 【大白话】：搞个折叠面板，展示团队疯狂甩锅、干活的过程
    with st.status("团队正在疯狂运转中...", expanded=True) as status:

        # 启动流水线，开始监听每个节点的动静
        for output in app.stream(inputs, config):
            for node_name, state_update in output.items():
                msg = state_update["messages"][-1].content

                # 【大白话】：根据当前是哪个打工人在动，网页上打出相应的“弹幕”
                if node_name == "researcher":
                    st.write("🕵️‍♂️ **[研究员]** 资料搜集完毕，正在移交撰稿人...")
                    with st.expander("查看原始资料"):
                        st.write(msg)

                elif node_name == "writer":
                    st.write("✍️ **[撰稿人]** 稿件已完成！战战兢兢地交由主编审核...")
                    # 💡 注意：每次写完都先假装它是终稿存起来，万一下一步过了呢？
                    final_article = msg
                    with st.expander("查看当前提交的草稿"):
                        st.write(msg)

                elif node_name == "editor":
                    if "【通过】" in msg:
                        st.success(f"🤬 **[主编]**：{msg}")  # 绿字表扬
                    else:
                        st.error(f"🤬 **[主编]**：{msg}")  # 红字痛骂
                        st.warning("🔄 触发重写机制！稿件已打回给撰稿人...")  # 提示循环发生了

        # 只要跳出上面那个循环，就说明走到了 END，完结撒花！
        status.update(label="任务完成！文章已过审！", state="complete", expanded=False)
        st.balloons()  # 网页飘气球特效！老板最爱！

        # 💡 新增这一行：立刻推送到微信群！
        # 💡 就在气球放完之后，紧接着加这三行代码！(注意缩进跟 st.balloons 对齐)
        st.write("正在尝试呼叫企业微信...")
        wx_result = publish_to_wechat(final_article)

        # 把企微的真实反应直接打在网页上，让 Bug 无处遁形！
        if wx_result.get("errcode") == 0:
            st.success("✅ 爆款文章已成功轰炸企业微信群！")
        else:
            st.error(f"❌ 发送失败，企微报错信息：{wx_result}")

    # 流水线彻底跑完后，把存下来的那篇最终过审稿子，正儿八经地打印出来
    st.divider()
    st.header("📰 正式发布文章")
    st.markdown(final_article)