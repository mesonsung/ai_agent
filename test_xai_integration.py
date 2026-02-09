#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 xAI 整合
"""

import os
import sys
from dotenv import load_dotenv

def test_environment():
    """測試環境變數"""
    print("=" * 60)
    print("1. 測試環境變數設定")
    print("=" * 60)
    
    load_dotenv()
    
    xai_api_key = os.getenv("XAI_API_KEY")
    xai_base_url = os.getenv("XAI_BASE_URL")
    xai_model = os.getenv("XAI_MODEL")
    embedding_model = os.getenv("EMBEDDING_MODEL")
    
    if not xai_api_key:
        print("❌ XAI_API_KEY 未設定")
        return False
    else:
        print(f"✅ XAI_API_KEY: {xai_api_key[:10]}...")
    
    print(f"✅ XAI_BASE_URL: {xai_base_url}")
    print(f"✅ XAI_MODEL: {xai_model}")
    print(f"✅ EMBEDDING_MODEL: {embedding_model}")
    print()
    return True

def test_embeddings():
    """測試 HuggingFace Embeddings"""
    print("=" * 60)
    print("2. 測試 HuggingFace Embeddings")
    print("=" * 60)
    
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        print("正在載入 HuggingFace Embeddings...")
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # 測試嵌入
        test_text = "這是一個測試文本"
        print(f"測試文本: {test_text}")
        
        embedding = embeddings.embed_query(test_text)
        print(f"✅ 嵌入向量維度: {len(embedding)}")
        print(f"✅ 嵌入向量前5個值: {embedding[:5]}")
        print()
        return True
        
    except Exception as e:
        print(f"❌ Embeddings 測試失敗: {e}")
        print()
        return False

def test_xai_api():
    """測試 xAI API 連接"""
    print("=" * 60)
    print("3. 測試 xAI API 連接")
    print("=" * 60)
    
    try:
        from langchain_community.chat_models import ChatOpenAI
        
        xai_api_key = os.getenv("XAI_API_KEY")
        xai_base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
        xai_model = os.getenv("XAI_MODEL", "grok-4-1-fast-reasoning")
        
        print(f"正在連接 xAI API...")
        print(f"模型: {xai_model}")
        
        llm = ChatOpenAI(
            model=xai_model,
            temperature=0.7,
            openai_api_key=xai_api_key,
            openai_api_base=xai_base_url
        )
        
        # 測試簡單查詢
        test_query = "請用一句話介紹什麼是人工智慧"
        print(f"測試查詢: {test_query}")
        
        response = llm.invoke(test_query)
        print(f"✅ xAI 回應: {response.content}")
        print()
        return True
        
    except Exception as e:
        print(f"❌ xAI API 測試失敗: {e}")
        print()
        return False

def test_vector_store():
    """測試向量資料庫"""
    print("=" * 60)
    print("4. 測試向量資料庫")
    print("=" * 60)
    
    try:
        from knowledge_base.vector_store import VectorStore
        
        print("正在初始化向量資料庫...")
        vector_store = VectorStore()
        
        # 測試添加文檔
        test_docs = [
            "Python 是一種高階程式語言",
            "機器學習是人工智慧的一個分支",
            "深度學習使用神經網路"
        ]
        
        print(f"添加 {len(test_docs)} 個測試文檔...")
        vector_store.add_texts(test_docs)
        
        # 測試搜尋
        query = "什麼是 Python"
        print(f"測試搜尋: {query}")
        
        results = vector_store.similarity_search(query, k=2)
        print(f"✅ 找到 {len(results)} 個相關文檔:")
        for i, doc in enumerate(results, 1):
            print(f"  {i}. {doc.page_content}")
        print()
        return True
        
    except Exception as e:
        print(f"❌ 向量資料庫測試失敗: {e}")
        print()
        return False

def test_document_loading():
    """測試文檔載入"""
    print("=" * 60)
    print("5. 測試文檔載入")
    print("=" * 60)
    
    try:
        from knowledge_base.document_processor import DocumentProcessor
        
        docs_dir = os.getenv("DOCUMENTS_DIRECTORY", "./knowledge_base/documents")
        print(f"文檔目錄: {docs_dir}")
        
        processor = DocumentProcessor(docs_dir)
        documents = processor.load_documents()
        
        print(f"✅ 成功載入 {len(documents)} 個文檔")
        
        # 顯示前幾個文檔
        if documents:
            print("\n前 3 個文檔片段:")
            for i, doc in enumerate(documents[:3], 1):
                content = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                print(f"  {i}. {content}")
                if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                    print(f"     來源: {doc.metadata['source']}")
        print()
        return True
        
    except Exception as e:
        print(f"❌ 文檔載入測試失敗: {e}")
        print()
        return False

def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("xAI 整合測試")
    print("=" * 60 + "\n")
    
    results = []
    
    # 執行測試
    results.append(("環境變數", test_environment()))
    results.append(("HuggingFace Embeddings", test_embeddings()))
    results.append(("xAI API", test_xai_api()))
    results.append(("向量資料庫", test_vector_store()))
    results.append(("文檔載入", test_document_loading()))
    
    # 顯示總結
    print("=" * 60)
    print("測試總結")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{name}: {status}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！xAI 整合成功！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 個測試失敗，請檢查配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())

