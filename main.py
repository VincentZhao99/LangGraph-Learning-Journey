import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from core.tools import get_current_time, multiply

load_dotenv()

# 初始化 DeepSeek 模型
model = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base=os.getenv("DEEPSEEK_BASE_URL"), # 这一行是关键
    max_tokens=1024
)

# 绑定工具
tools = [get_current_time, multiply]
model_with_tools = model.bind_tools(tools)

# 尝试调用
res = model_with_tools.invoke("现在几点？并算一下 42*13")
print(res.tool_calls)

# 模拟：假设 LLM 已经返回了 tool_calls
mock_tool_calls = [{'name': 'multiply', 'args': {'a': 42, 'b': 13}, 'id': 'call_123'}]

def handle_tool_calls(tool_calls):
    for call in tool_calls:
        if call['name'] == 'multiply':
            # 真正去运行你在 core/tools.py 里的函数
            result = multiply.invoke(call['args'])
            print(f"成功执行工具！结果是: {result}")

handle_tool_calls(mock_tool_calls)