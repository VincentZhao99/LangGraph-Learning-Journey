import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from core.tools import get_current_time, multiply
from langgraph.prebuilt import create_react_agent # 2026年最高效的预构建组件

load_dotenv()

# 1. 依然使用你昨天配好的 DeepSeek (或 Gemini)
model = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL"),
)

# 2. 定义工具列表
tools = [get_current_time, multiply]

# 3. 【核心】创建 LangGraph 代理
# 它会自动帮你处理：调用模型 -> 发现tool_calls -> 执行工具 -> 反馈结果 -> 再次调用模型
agent_executor = create_react_agent(model, tools)

# 4. 运行并查看完整的对话轨迹
query = {"messages": [("user", "现在几点？并算一下 42*13")]}

# 使用 stream 模式可以看到 Agent 思考的每一步
for chunk in agent_executor.stream(query):
    print(chunk)
    print("-" * 30)