import sqlite3
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def inspect_sqlite():
    print("=== 🧠 SQLite 记忆库开箱 ===")
    # 注意：确认你的 sqlite 文件路径是否正确（这里假设在 data 目录下）
    db_path = "data/checkpoints.sqlite"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. 看看 LangGraph 在里面建了什么表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📚 数据库里的表: {tables}")

        # 2. 看看 checkpoints 表里存的记忆 ID
        # LangGraph 主要把数据存在 checkpoints 表中
        cursor.execute("SELECT thread_id, checkpoint_id FROM checkpoints LIMIT 5;")
        rows = cursor.fetchall()
        print(f"🧵 最近的 5 条对话记忆记录:")
        for row in rows:
            print(f"   - 对话线程: {row[0]}, 存档节点: {row[1]}")

    except Exception as e:
        print(f"❌ 读取 SQLite 失败: {e}")

def inspect_faiss():
    print("\n=== 📚 FAISS 知识库开箱 ===")

    # 1. 必须用和当时存入时一模一样的“翻译官”
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 注意：确认你的 FAISS 文件夹路径（这里假设叫 faiss_index 且和脚本同级）
    faiss_path = "faiss_index"

    try:
        # 💡 allow_dangerous_deserialization=True 是必须的，因为我们要读取本地的 pkl 缓存文件
        vector_store = FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)

        # 获取里面总共切了多少个文本块
        total_chunks = vector_store.index.ntotal
        print(f"🔪 你的 PDF 一共被切成了 {total_chunks} 个文本块！\n")

        # 遍历底层的 docstore，偷看前 3 个文本块到底长什么样
        print("👇 前 3 个文本块的真实内容：")
        for i, (doc_id, doc) in enumerate(list(vector_store.docstore._dict.items())[:3]):
            print(f"【片段 {i + 1} ID】: {doc_id}")
            # 只打印前 100 个字符意思一下
            print(f"【片段 {i + 1} 内容】: {doc.page_content[:100]}...\n")

    except Exception as e:
        print(f"❌ 读取 FAISS 失败: {e}")


if __name__ == "__main__":
    # inspect_sqlite()
    inspect_faiss()
