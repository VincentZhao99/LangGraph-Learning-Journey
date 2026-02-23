# core/ingest.py
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


def build_vector_store():
    print("🚀 开始离线构建知识库...")

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_path = os.path.join(BASE_DIR, "data", "my_notes.pdf")
    db_path = os.path.join(BASE_DIR, "data", "faiss_index")  # 👈 我们要把向量存在这里

    if not os.path.exists(pdf_path):
        print(f"❌ 找不到文件: {pdf_path}")
        return

    # 1. 加载与切片
    print("📄 正在读取和切分 PDF...")
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)

    # 2. Embedding 转换
    print("🧠 正在使用本地模型计算向量 (这需要一点时间)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 3. 构建并【存入硬盘】
    print("💾 正在将向量库持久化到硬盘...")
    vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
    vectorstore.save_local(db_path)

    print(f"✅ 知识库构建完成！已保存在: {db_path}")


if __name__ == "__main__":
    build_vector_store()