"""使用範例 - 展示如何程式化使用智識庫"""

import os
from dotenv import load_dotenv
from knowledge_base.vector_store import VectorStore
from knowledge_base.document_processor import DocumentProcessor
from knowledge_base.agent import KnowledgeAgent


def main():
    """主函數"""
    # 載入環境變數
    load_dotenv()
    
    # 檢查 API 金鑰
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 請設定 OPENAI_API_KEY 環境變數")
        return
    
    print("=" * 60)
    print("個人智識庫 AI Agent - 使用範例".center(60))
    print("=" * 60)
    
    # 1. 初始化向量資料庫
    print("\n步驟 1: 初始化向量資料庫")
    vector_store = VectorStore(
        persist_directory="./knowledge_base/data/chroma",
        embedding_model="text-embedding-3-small"
    )
    
    # 2. 初始化文件處理器
    print("\n步驟 2: 初始化文件處理器")
    doc_processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
    
    # 3. 載入並處理文件
    print("\n步驟 3: 載入範例文件")
    documents = doc_processor.process_file("./knowledge_base/documents/example.txt")
    
    # 4. 新增文件到向量資料庫
    print("\n步驟 4: 新增文件到向量資料庫")
    if documents:
        vector_store.add_documents(documents)
    
    # 5. 初始化 AI Agent
    print("\n步驟 5: 初始化 AI Agent")
    agent = KnowledgeAgent(
        vector_store=vector_store,
        model_name="gpt-4-turbo-preview",
        verbose=False  # 設為 True 可以看到詳細的思考過程
    )
    
    # 6. 測試查詢
    print("\n步驟 6: 測試查詢")
    print("=" * 60)
    
    questions = [
        "什麼是機器學習？",
        "深度學習有哪些常見的架構？",
        "機器學習面臨哪些挑戰？"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n問題 {i}: {question}")
        print("-" * 60)
        answer = agent.query(question)
        print(f"回答: {answer}")
        print("=" * 60)
    
    # 7. 測試直接搜尋（不使用 Agent）
    print("\n步驟 7: 測試直接向量搜尋")
    print("-" * 60)
    search_results = vector_store.similarity_search("深度學習", k=2)
    for i, doc in enumerate(search_results, 1):
        print(f"\n搜尋結果 {i}:")
        print(f"內容: {doc.page_content[:200]}...")
        print(f"來源: {doc.metadata.get('source', '未知')}")
    
    print("\n" + "=" * 60)
    print("範例執行完成！".center(60))
    print("=" * 60)


if __name__ == "__main__":
    main()

