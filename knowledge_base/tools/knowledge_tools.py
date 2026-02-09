"""智識庫相關工具"""

from typing import Optional, Type, Any
from langchain_core.tools import BaseTool
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel, Field, ConfigDict


class KnowledgeSearchInput(BaseModel):
    """智識庫搜尋工具的輸入模型"""
    query: str = Field(description="要搜尋的問題或關鍵字")
    k: int = Field(default=4, description="返回的結果數量")


class KnowledgeSearchTool(BaseTool):
    """智識庫搜尋工具"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "knowledge_search"
    description: str = """
    在個人智識庫中搜尋相關資訊。
    當你需要查找已儲存的文件、筆記或知識時使用此工具。
    輸入一個問題或關鍵字，工具會返回最相關的內容。
    """
    args_schema: Type[BaseModel] = KnowledgeSearchInput
    vector_store: Any = None  # 將在初始化時設定
    
    def _run(
        self,
        query: str,
        k: int = 4,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """執行搜尋"""
        if self.vector_store is None:
            return "錯誤：向量資料庫未初始化"
        
        try:
            # 執行相似度搜尋
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            if not results:
                return "未找到相關資訊"
            
            # 格式化結果
            formatted_results = []
            for i, (doc, score) in enumerate(results, 1):
                source = doc.metadata.get('source', '未知來源')
                content = doc.page_content
                formatted_results.append(
                    f"結果 {i} (相關度: {1-score:.2f}):\n"
                    f"來源: {source}\n"
                    f"內容: {content}\n"
                )
            
            return "\n".join(formatted_results)
        
        except Exception as e:
            return f"搜尋時發生錯誤: {str(e)}"


class DocumentSummaryInput(BaseModel):
    """文件摘要工具的輸入模型"""
    topic: str = Field(description="要摘要的主題或文件名稱")


class DocumentSummaryTool(BaseTool):
    """文件摘要工具"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "document_summary"
    description: str = """
    獲取智識庫中特定主題或文件的摘要。
    當你需要快速了解某個主題的概要時使用此工具。
    """
    args_schema: Type[BaseModel] = DocumentSummaryInput
    vector_store: Any = None
    llm: Any = None
    
    def _run(
        self,
        topic: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """執行摘要"""
        if self.vector_store is None or self.llm is None:
            return "錯誤：工具未正確初始化"
        
        try:
            # 搜尋相關文件
            results = self.vector_store.similarity_search(topic, k=5)
            
            if not results:
                return f"未找到關於「{topic}」的相關資訊"
            
            # 合併內容
            combined_content = "\n\n".join([doc.page_content for doc in results])
            
            # 使用 LLM 生成摘要
            prompt = f"""請根據以下內容，提供一個簡潔的摘要：

{combined_content}

摘要："""
            
            summary = self.llm.predict(prompt)
            return summary
        
        except Exception as e:
            return f"生成摘要時發生錯誤: {str(e)}"

