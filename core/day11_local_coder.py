# 文件路径：day11_local_coder.py
import os
import warnings
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# 屏蔽烦人的警告
warnings.filterwarnings("ignore")
load_dotenv()

# 🧰 导入咱们这几天攒下的所有神兵利器！
from core.tools import multiply, get_current_time, web_search_tool
from core.rag_tool import query_knowledge_base
from core.code_tool import execute_python_code  # 👈 今天刚打造的核武器

# 1. 雇佣底层大模型
model = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
)

# 2. 把所有工具打包成一个武器库
tools = [multiply, get_current_time, web_search_tool, query_knowledge_base, execute_python_code]

# 3. 紧箍咒 / 员工手册
SYSTEM_PROMPT = """你是一个顶级的全能 AI 工程师。
你可以自由使用你拥有的工具来完成用户的任务。
如果任务涉及到复杂的计算、数据处理或本地文件操作，请毫不犹豫地使用 execute_python_code 工具自己写代码解决！
"""

# 4. 生成 Agent
agent = create_react_agent(model, tools, prompt=SYSTEM_PROMPT)

print("🤖 你的专属全能本地 AI 程序员已上线！(输入 'quit' 退出)")
print("-" * 50)

# 5. 极简的命令行交互循环
while True:
    user_input = input("\n👤 你的指令: ")
    if user_input.lower() in ['quit', 'exit', 'q']:
        print("拜拜！")
        break

    print("🤖 Agent 思考中...")
    inputs = {"messages": [("user", user_input)]}

    # 打印流转过程，让你看看它是怎么调工具的
    for event in agent.stream(inputs):
        if "agent" in event:
            msg = event["agent"]["messages"][-1]
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_names = [t["name"] for t in msg.tool_calls]
                print(f"  🛠️  正在使用工具: {', '.join(tool_names)} ...")

        elif "tools" in event:
            # 打印工具执行的结果
            tool_msg = event["tools"]["messages"][-1]
            print(f"  ✅  工具返回结果已收到。")

    # 打印最终回复
    final_reply = event["agent"]["messages"][-1].content if "agent" in event else ""
    print(f"\n💡 最终回复:\n{final_reply}")