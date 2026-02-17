import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from core.tools import multiply, get_current_time
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import ToolMessage

load_dotenv()

# --- 1. 初始化 (保持不变) ---
model = ChatOpenAI(model='deepseek-chat', openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
                   openai_api_base=os.getenv("DEEPSEEK_BASE_URL"))
memory = MemorySaver()
app = create_react_agent(model, tools=[multiply, get_current_time], checkpointer=memory, interrupt_before=["tools"])
config = {"configurable": {"thread_id": "vincents_dynamic_agent_001"}}

print("🤖 Agent 已上线！(输入 'exit' 或 'q' 退出对话)")

# --- 2. 动态交互主循环 ---
while True:
    # A. 接收客户的动态输入
    user_query = input("\n👤 你的指令: ")
    if user_query.lower() in ['exit', 'q', 'quit']:
        print("Bye!")
        break

    # 构造输入消息
    inputs = {"messages": [("user", user_query)]}

    # B. 处理这个指令产生的任务流 (包括自动思考和手动审批)
    while True:
        # 运行直到【中断】或【任务结束】
        for event in app.stream(inputs, config):
            # 打印关键过程 (可选，生产环境可以只打印回复)
            if "agent" in event:
                msg = event["agent"]["messages"][-1]
                if msg.content:
                    print(f"🤖 AI: {msg.content}")
                if msg.tool_calls:
                    print(f"👉 AI 申请调用工具: {[t['name'] for t in msg.tool_calls]}")

        # 检查当前状态：是否被 interrupt_before 拦住了？
        state = app.get_state(config)

        if not state.next:
            # 这一轮任务彻底跑完了，回到外层循环等用户提新问题
            break

        # 如果 state.next 有值，说明它在等工具审批
        approval = input("⚠️ 是否批准执行工具? (y=批准 / n=拒绝并解释原因): ")

        if approval.lower() == 'y':
            inputs = None  # 传 None 表示从断点继续执行原计划
            print("🚀 批准通过...")
        else:
            reason = input("📝 请输入拒绝原因 (AI 会根据你的反馈重新思考): ")
            # 伪造 ToolMessage 结案，消除报错风险
            last_msg = state.values["messages"][-1]
            for tool_call in last_msg.tool_calls:
                app.update_state(
                    config,
                    {"messages": [ToolMessage(content=f"操作被拒绝：{reason}", tool_call_id=tool_call["id"])]},
                    as_node="tools"
                )
            # 重新激活 Agent 思考
            inputs = {"messages": [("user", f"我不批准刚才的操作，原因是：{reason}。请重新处理。")]}