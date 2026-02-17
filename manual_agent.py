from core.tools import tools_map


def execute_tools(tool_calls):
    """
    Agent 的执行器：
    1. 接收 AI 想调用的工具列表
    2. 找到对应的 Python 函数
    3. 执行并返回结果
    """
    responses = []
    for call in tool_calls:
        tool_name = call["name"]
        tool_args = call["args"]

        print(f"📡 正在调用工具: {tool_name}, 参数: {tool_args}")

        # 从字典中找到函数并运行
        if tool_name in tools_map:
            selected_tool = tools_map[tool_name]
            # .invoke 是 LangChain 工具的标准触发方式
            observation = selected_tool.invoke(tool_args)
            responses.append({
                "tool_call_id": call["id"],
                "output": observation
            })
    return responses


# --- 模拟测试 ---
# 假设这是 Gemini/DeepSeek 返回给我们的意图
mock_res = [
    {"name": "multiply", "args": {"a": 42, "b": 13}, "id": "call_001"},
    {"name": "get_current_time", "args": {}, "id": "call_002"}
]

print("🚀 开始模拟 Agent 执行...")
results = execute_tools(mock_res)
for r in results:
    print(f"✅ 工具返回结果: {r['output']}")