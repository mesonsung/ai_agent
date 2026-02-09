"""文件處理模組 - 載入和分割各種格式的文件"""

import os
from typing import List
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader
)


class DocumentProcessor:
    """文件處理器類"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化文件處理器
        
        Args:
            chunk_size: 文件分割大小
            chunk_overlap: 分割重疊大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        # 支援的文件格式
        self.supported_extensions = {
            '.txt': TextLoader,
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.md': UnstructuredMarkdownLoader,
        }
    
    def load_document(self, file_path: str) -> List[Document]:
        """
        載入單個文件
        
        Args:
            file_path: 文件路徑
            
        Returns:
            文件列表
        """
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension not in self.supported_extensions:
            raise ValueError(f"不支援的文件格式: {file_extension}")
        
        loader_class = self.supported_extensions[file_extension]
        
        try:
            loader = loader_class(file_path)
            documents = loader.load()
            print(f"✓ 已載入文件: {file_path}")
            return documents
        except Exception as e:
            print(f"✗ 載入文件失敗 {file_path}: {e}")
            return []
    
    def load_directory(self, directory_path: str) -> List[Document]:
        """
        載入目錄中的所有支援文件
        
        Args:
            directory_path: 目錄路徑
            
        Returns:
            文件列表
        """
        all_documents = []
        directory = Path(directory_path)
        
        if not directory.exists():
            print(f"✗ 目錄不存在: {directory_path}")
            return []
        
        # 遍歷目錄中的所有文件
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                documents = self.load_document(str(file_path))
                all_documents.extend(documents)
        
        print(f"✓ 從目錄載入了 {len(all_documents)} 個文件")
        return all_documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        分割文件為較小的片段
        
        Args:
            documents: 文件列表
            
        Returns:
            分割後的文件片段列表
        """
        if not documents:
            return []
        
        split_docs = self.text_splitter.split_documents(documents)
        print(f"✓ 已將文件分割為 {len(split_docs)} 個片段")
        return split_docs
    
    def process_file(self, file_path: str) -> List[Document]:
        """
        處理單個文件（載入並分割）
        
        Args:
            file_path: 文件路徑
            
        Returns:
            處理後的文件片段列表
        """
        documents = self.load_document(file_path)
        return self.split_documents(documents)
    
    def process_directory(self, directory_path: str) -> List[Document]:
        """
        處理目錄中的所有文件（載入並分割）
        
        Args:
            directory_path: 目錄路徑
            
        Returns:
            處理後的文件片段列表
        """
        documents = self.load_directory(directory_path)
        return self.split_documents(documents)
    
    def get_supported_formats(self) -> List[str]:
        """獲取支援的文件格式列表"""
        return list(self.supported_extensions.keys())

