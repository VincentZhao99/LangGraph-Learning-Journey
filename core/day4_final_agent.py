import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from core.tools import multiply, get_current_time
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver # 💡 新增：内存记忆件

load_dotenv()

# 1. 初始化模型
model = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL"),
)

# 2. 准备记忆“存储卡”
# 这里的 MemorySaver 会把对话历史存在内存里
memory = MemorySaver()

# 3. 创建带记忆的 Agent
# checkpointer 参数是关键，它让 Agent 拥有了“状态”
app = create_react_agent(model, tools=[multiply, get_current_time], checkpointer=memory)

# 4. 模拟多轮对话
# config 里的 thread_id 就像是“聊天室 ID”
config = {"configurable": {"thread_id": "vincents_chat_001"}}

print("--- 第一轮对话 ---")
input_1 = {"messages": [("user", "算一下 42 乘以 13")]}
for chunk in app.stream(input_1, config):
    print(chunk)

print("\n--- 第二轮对话（测试记忆） ---")
# 注意：这里我们没提 546，但 Agent 应该记得
input_2 = {"messages": [("user", "再加上 10 等于多少？")]}
for chunk in app.stream(input_2, config):
    print(chunk)

# 获取当前线程的最新状态
current_state = app.get_state(config)
print("--- 内存里的秘密 ---")
print(current_state.values["messages"]) # 打印出它记得的所有对话