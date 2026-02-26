import os
import warnings
import logging  # 💡 新增：引入 Python 内置的日志模块
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# 屏蔽烦人的警告
warnings.filterwarnings("ignore")
load_dotenv()

from core.tools import multiply, get_current_time, web_search_tool
from core.rag_tool import query_knowledge_base
from core.code_tool import execute_python_code

# ==========================================
# 💡 核心升级：配置日志监控系统
# ==========================================
logging.basicConfig(
    filename='agent_run.log',  # 日志将保存在这个文件里
    level=logging.INFO,
    format='\n' + '=' * 40 + '\n%(asctime)s - %(levelname)s\n%(message)s',
    encoding='utf-8'  # 防止中文乱码
)

model = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
)

tools = [multiply, get_current_time, web_search_tool, query_knowledge_base, execute_python_code]

# 💡 给系统提示词加上“省钱防坑”指令
SYSTEM_PROMPT = """你是一个顶级的全能 AI 工程师。
你可以自由使用你拥有的工具来完成用户的任务。
如果任务涉及到复杂的计算或数据处理，请毫不犹豫地使用 execute_python_code 工具自己写代码解决！
【⚠️省Token警告】：分析数据时，绝对不要打印整个 DataFrame！只能用 df.head() 或 df.info() 查看结构。把最终结果直接保存为文件！
"""

agent = create_react_agent(model, tools, prompt=SYSTEM_PROMPT)

print("🤖 你的专属全能本地 AI 程序员已上线！(已开启后台日志记录)")
print("-" * 50)

while True:
    user_input = input("\n👤 你的指令: ")
    if user_input.lower() in ['quit', 'exit', 'q']:
        print("拜拜！")
        break

    print("🤖 Agent 思考中...")
    logging.info(f"👤 用户输入: {user_input}")  # 记录你的问题

    inputs = {"messages": [("user", user_input)]}

    # 打印流转过程，并写入日志
    for event in agent.stream(inputs):
        if "agent" in event:
            msg = event["agent"]["messages"][-1]
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call.get("args", {})

                    print(f"  🛠️  正在调用工具: {tool_name} ... (代码已写入日志)")

                    # 💡 核心抓取：把 AI 写的代码原封不动地记在日志里！
                    if tool_name == "execute_python_code" and "code" in tool_args:
                        logging.info(f"💻 AI 编写的 Python 代码:\n{tool_args['code']}")
                    else:
                        logging.info(f"🛠️ AI 调用工具参数:\n{tool_args}")

        elif "tools" in event:
            tool_msg = event["tools"]["messages"][-1]
            print(f"  ✅  工具执行完毕。(结果已写入日志)")
            # 💡 记录代码执行的真实输出（或报错）
            logging.info(f"✅ 工具返回结果:\n{tool_msg.content}")

    final_reply = event["agent"]["messages"][-1].content if "agent" in event else ""
    print(f"\n💡 最终回复:\n{final_reply}")
    logging.info(f"💡 最终回复:\n{final_reply}")