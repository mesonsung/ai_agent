"""向量資料庫模組 - 使用 ChromaDB 儲存和檢索文件"""

import os
from typing import List, Optional

# 關閉 ChromaDB telemetry 以避免警告訊息
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import chromadb
from chromadb.config import Settings

# 設定 ChromaDB 關閉 telemetry
chromadb_settings = Settings(
    anonymized_telemetry=False,
    allow_reset=True
)

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document


class VectorStore:
    """向量資料庫管理類"""

    def __init__(self, persist_directory: str, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        初始化向量資料庫

        Args:
            persist_directory: 資料庫持久化目錄
            embedding_model: 嵌入模型名稱 (使用 HuggingFace 模型)
        """
        self.persist_directory = persist_directory

        # 使用 HuggingFace Embeddings (本地運行，不需要 API 金鑰)
        print(f"📥 正在載入嵌入模型: {embedding_model}...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("✓ 嵌入模型載入完成")

        self.vectorstore = None

        # 確保目錄存在
        os.makedirs(persist_directory, exist_ok=True)

        # 載入或建立向量資料庫
        self._load_or_create_vectorstore()
    
    def _load_or_create_vectorstore(self):
        """載入現有的向量資料庫或建立新的"""
        try:
            # 建立 ChromaDB client 並關閉 telemetry
            client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=chromadb_settings
            )
            self.vectorstore = Chroma(
                client=client,
                embedding_function=self.embeddings
            )
            print(f"✓ 已載入向量資料庫，目前有 {self.vectorstore._collection.count()} 個文件片段")
        except Exception as e:
            print(f"建立新的向量資料庫: {e}")
            client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=chromadb_settings
            )
            self.vectorstore = Chroma(
                client=client,
                embedding_function=self.embeddings
            )
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        新增文件到向量資料庫
        
        Args:
            documents: 文件列表
            
        Returns:
            文件 ID 列表
        """
        if not documents:
            return []
        
        ids = self.vectorstore.add_documents(documents)
        print(f"✓ 已新增 {len(documents)} 個文件片段到向量資料庫")
        return ids
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """
        相似度搜尋
        
        Args:
            query: 查詢文字
            k: 返回結果數量
            
        Returns:
            相關文件列表
        """
        results = self.vectorstore.similarity_search(query, k=k)
        return results
    
    def similarity_search_with_score(self, query: str, k: int = 4) -> List[tuple]:
        """
        帶分數的相似度搜尋
        
        Args:
            query: 查詢文字
            k: 返回結果數量
            
        Returns:
            (文件, 分數) 元組列表
        """
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return results
    
    def delete_collection(self):
        """刪除整個集合"""
        if self.vectorstore:
            self.vectorstore.delete_collection()
            print("✓ 已刪除向量資料庫")
    
    def get_retriever(self, search_kwargs: Optional[dict] = None):
        """
        獲取檢索器
        
        Args:
            search_kwargs: 搜尋參數
            
        Returns:
            檢索器物件
        """
        if search_kwargs is None:
            search_kwargs = {"k": 4}
        
        return self.vectorstore.as_retriever(search_kwargs=search_kwargs)

