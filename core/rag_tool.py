# core/rag_tool.py
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.tools import tool

# ⚠️ 注意：为了性能，Embedding 模型在工具外部初始化，这样启动 Agent 时只加载一次
print("⏳ 正在加载检索模型准备待命...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


@tool
def query_knowledge_base(query: str):
    """当需要查询本地 PDF/私有知识库内容时，使用此工具。"""

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(BASE_DIR, "data", "faiss_index")

    if not os.path.exists(db_path):
        return "错误：本地知识库未建立。请管理员先运行 ingest.py。"

    # 1. 直接从硬盘加载向量库 (毫秒级)
    # allow_dangerous_deserialization=True 是 FAISS 加载本地文件的必须安全确认
    vectorstore = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)

    # 2. 闪电检索
    print(f"\n🔍 [RAG检索中] 搜索词: {query}")
    results = vectorstore.similarity_search(query, k=3)

    if not results:
        return "本地文档中没有找到相关信息。"

    context = "\n---\n".join([doc.page_content for doc in results])
    return f"从私有知识库中找到以下相关片段：\n{context}"