import os
from dotenv import load_dotenv # 👈 确保安装了 python-dotenv
from langchain_community.tools.tavily_search import TavilySearchResults

# 1. 显式加载 .env 文件
load_dotenv()

print(f"✅ 环境变量加载尝试完成")
print(f"DEBUG: TAVILY_API_KEY 是否存在: {'是' if os.getenv('TAVILY_API_KEY') else '否'}")

try:
    # 2. 现在初始化就不会报错了
    search = TavilySearchResults(k=1)
    print("✅ Tavily 工具初始化成功！")
except Exception as e:
    print(f"❌ Tavily 初始化失败: {e}")