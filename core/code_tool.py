# 文件路径：core/code_tool.py
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

# 【大白话】：这是 LangChain 提供的一个 Python 代码解释器环境，相当于一个虚拟的命令行
repl = PythonREPL()

@tool
def execute_python_code(code: str) -> str:
    """
    一个能在本地执行 Python 代码的工具。
    【使用规则】：
    1. 当你需要进行复杂的数学计算、处理大量数据、或者生成本地文件时，请编写完整的 Python 代码并交由该工具执行。
    2. 必须且只能输入合法的 Python 代码字符串。
    3. 如果代码需要输出结果，请确保代码中包含 print() 语句。
    """
    try:
        # 【大白话】：让 AI 把生成的代码扔进这个解释器里跑，把控制台打印出来的结果抓回来
        result = repl.run(code)
        return f"✅ 代码执行成功，控制台输出结果如下:\n{result}"
    except Exception as e:
        # 【大白话】：如果 AI 代码写得有 Bug（比如语法错误），把报错信息丢回给它，让它自己修！
        return f"❌ 代码执行报错，请根据以下错误信息修改代码:\n{e}"