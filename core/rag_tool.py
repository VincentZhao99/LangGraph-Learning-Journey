import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# 替换为 HuggingFace 导入
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.tools import tool

# 1. 初始化本地 Embedding 模型 (完全免费，本地运行)
# 第一次运行会从 HuggingFace 下载模型文件
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


@tool
def query_knowledge_base(query: str):
    """当需要查询本地 PDF 文档内容时使用此工具。"""

    # 获取 PDF 路径（建议使用 data 文件夹下的文件）
    pdf_path = "data/my_notes.pdf"

    if not os.path.exists(pdf_path):
        return f"错误：找不到文件 {pdf_path}，请确保 data 文件夹下有此 PDF。"

    # 2. 加载文档
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    # 3. 文档切片
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)

    # 4. 构建本地向量数据库 (内存版)
    vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)

    # 5. 检索最相关的 3 片内容
    results = vectorstore.similarity_search(query, k=3)

    context = "\n\n".join([doc.page_content for doc in results])
    return f"从本地文档中找到的相关内容如下：\n{context}"