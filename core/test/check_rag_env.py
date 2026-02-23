import sys
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


def test_rag_setup():
    print("🚀 开始 RAG 环境自检...")

    try:
        # 1. 测试 Embedding 模型下载与初始化
        print("📥 正在加载本地 Embedding 模型 (all-MiniLM-L6-v2)...")
        print("💡 第一次运行可能需要下载模型，请稍候...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        print("✅ Embedding 模型加载成功！")

        # 2. 模拟一些文档数据
        test_docs = [
            Document(page_content="我的名字叫 Vincent，我正在学习 AI Agent。"),
            Document(page_content="LangGraph 是一个用于构建循环多智能体系统的库。"),
            Document(page_content="今天的天气非常适合在家里写代码。")
        ]

        # 3. 测试向量数据库构建
        print("🔨 正在尝试构建内存向量库 FAISS...")
        vectorstore = FAISS.from_documents(test_docs, embeddings)
        print("✅ FAISS 向量库构建成功！")

        # 4. 测试相似度搜索
        print("🔍 正在执行测试搜索: '谁在学习 Agent？'")
        query = "谁在学习 Agent？"
        results = vectorstore.similarity_search(query, k=1)

        if len(results) > 0:
            print(f"✅ 搜索功能正常！匹配结果: '{results[0].page_content}'")
            print("\n🎉 结论：你的 RAG 环境已准备就绪！")
        else:
            print("❌ 搜索未返回结果，请检查逻辑。")

    except Exception as e:
        print(f"\n❌ 环境检查失败！错误信息如下：\n{str(e)}")
        print("\n💡 提示：如果报错说找不到模块，请确认是否运行了 python3 -m pip install ...")


if __name__ == "__main__":
    test_rag_setup()