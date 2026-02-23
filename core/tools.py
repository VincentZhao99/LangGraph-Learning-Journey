from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

@tool
def get_current_time() -> str:
    """获取当前系统的具体时间。"""
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def multiply(a: int, b: int) -> int:
    """计算两个整数的乘积。"""
    return a * b

# 定义一个便捷列表，方便后续查找
tools_list = [multiply, get_current_time]
# 将工具映射为字典，方便按名称查找：{"multiply": multiply_func, ...}
tools_map = {tool.name: tool for tool in tools_list}

# 定义搜索工具，设置 k=3 表示返回最相关的 3 条结果
web_search_tool = TavilySearchResults(k=1)
# 你可以先本地测试一下
# print(web_search_tool.invoke("2026年2月DeepSeek最新动态"))