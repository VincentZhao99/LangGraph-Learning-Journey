import os
from core.rag_tool import query_knowledge_base


def run_test():
    print("🧪 开始测试 RAG 检索工具...\n")

    # 1. 检查前置条件：数据库是否真的建好了？
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "data", "faiss_index")

    if not os.path.exists(db_path):
        print(f"❌ 严重错误：找不到 FAISS 向量库！")
        print(f"👉 请先运行: .venv/bin/python3 core/ingest.py 来构建知识库。")
        return

    # 2. 模拟 Agent 调用工具
    test_query = "请问能在五星级酒店开会吗？"  # 换成你 PDF 里确实存在的内容
    print(f"🗣️ 模拟提问: '{test_query}'")

    try:
        # 直接 invoke 工具，就像 Agent 做的那样
        result = query_knowledge_base.invoke(test_query)

        print("\n✅ 工具返回结果如下：")
        print("=" * 40)
        print(result)
        print("=" * 40)
        print("\n🎉 测试通过！你的 rag_tool.py 路径和逻辑完美无缺，可以安全接入 Agent 了。")

    except Exception as e:
        print(f"\n❌ 工具运行崩溃，错误信息: {e}")


if __name__ == "__main__":
    run_test()