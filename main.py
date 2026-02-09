"""個人智識庫 AI Agent 主程式"""

import os
import sys
import warnings
import logging

# 在任何其他 import 之前關閉 ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

# 過濾 ChromaDB telemetry 警告
warnings.filterwarnings("ignore", message=".*telemetry.*")
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)

# 暫時抑制 chromadb telemetry 錯誤訊息
class _SuppressTelemetryPrint:
    """暫時抑制 telemetry 相關的 print 輸出"""
    def __init__(self):
        self._original_print = None

    def __enter__(self):
        import builtins
        self._original_print = builtins.print
        def filtered_print(*args, **kwargs):
            msg = ' '.join(str(a) for a in args)
            if 'telemetry' not in msg.lower():
                self._original_print(*args, **kwargs)
        builtins.print = filtered_print
        return self

    def __exit__(self, *args):
        import builtins
        builtins.print = self._original_print

from pathlib import Path
from dotenv import load_dotenv

from knowledge_base.vector_store import VectorStore
from knowledge_base.document_processor import DocumentProcessor
from knowledge_base.agent import KnowledgeAgent


class KnowledgeBaseApp:
    """智識庫應用程式"""
    
    def __init__(self):
        """初始化應用程式"""
        # 載入環境變數
        load_dotenv()

        # 檢查 API 金鑰
        if not os.getenv("XAI_API_KEY"):
            print("❌ 錯誤：請在 .env 檔案中設定 XAI_API_KEY")
            print("💡 提示：請訪問 https://console.x.ai/ 獲取 xAI API 金鑰")
            sys.exit(1)

        # 初始化配置
        self.persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "./knowledge_base/data/chroma")
        self.documents_directory = os.getenv("DOCUMENTS_DIRECTORY", "./knowledge_base/documents")
        self.model_name = os.getenv("XAI_MODEL", "grok-beta")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.max_iterations = int(os.getenv("MAX_ITERATIONS", "10"))
        self.verbose = os.getenv("VERBOSE", "true").lower() == "true"
        
        # 初始化組件
        print("🚀 正在初始化個人智識庫...")
        with _SuppressTelemetryPrint():
            self.vector_store = VectorStore(self.persist_directory, self.embedding_model)
        self.document_processor = DocumentProcessor()
        self.agent = KnowledgeAgent(
            vector_store=self.vector_store,
            model_name=self.model_name,
            max_iterations=self.max_iterations,
            verbose=self.verbose
        )
        print("✓ 初始化完成！\n")
    
    def add_documents(self, path: str):
        """新增文件到智識庫"""
        path_obj = Path(path)
        
        if not path_obj.exists():
            print(f"❌ 路徑不存在: {path}")
            return
        
        print(f"📄 正在處理文件...")
        
        if path_obj.is_file():
            documents = self.document_processor.process_file(str(path_obj))
        else:
            documents = self.document_processor.process_directory(str(path_obj))
        
        if documents:
            self.vector_store.add_documents(documents)
            print(f"✓ 成功新增文件到智識庫！\n")
        else:
            print("❌ 沒有找到可處理的文件\n")
    
    def query(self, question: str):
        """查詢智識庫"""
        print(f"\n💭 問題: {question}")
        print("🤔 思考中...\n")
        
        answer = self.agent.query(question)
        
        print(f"\n💡 回答:\n{answer}\n")
    
    def show_menu(self):
        """顯示選單"""
        print("=" * 60)
        print("個人智識庫 AI Agent".center(60))
        print("=" * 60)
        print("\n可用指令：")
        print("  1. add <路徑>     - 新增文件或目錄到智識庫")
        print("  2. query          - 向智識庫提問")
        print("  3. clear          - 清除對話記憶")
        print("  4. formats        - 顯示支援的文件格式")
        print("  5. help           - 顯示此選單")
        print("  6. exit           - 退出程式")
        print("=" * 60 + "\n")
    
    def run(self):
        """執行主程式"""
        self.show_menu()
        
        while True:
            try:
                user_input = input("👤 請輸入指令: ").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()
                
                if command == "exit" or command == "quit":
                    print("\n👋 再見！")
                    break
                
                elif command == "help":
                    self.show_menu()
                
                elif command == "add":
                    if len(parts) < 2:
                        print("❌ 請指定文件或目錄路徑")
                    else:
                        self.add_documents(parts[1])
                
                elif command == "query":
                    question = input("💭 請輸入您的問題: ").strip()
                    if question:
                        self.query(question)
                
                elif command == "clear":
                    self.agent.clear_memory()
                
                elif command == "formats":
                    formats = self.document_processor.get_supported_formats()
                    print(f"\n支援的文件格式: {', '.join(formats)}\n")
                
                else:
                    # 直接當作問題處理
                    self.query(user_input)
            
            except KeyboardInterrupt:
                print("\n\n👋 再見！")
                break
            except Exception as e:
                print(f"\n❌ 發生錯誤: {e}\n")


if __name__ == "__main__":
    app = KnowledgeBaseApp()
    app.run()

