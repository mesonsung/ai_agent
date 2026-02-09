"""測試安裝是否成功"""

import sys


def test_imports():
    """測試所有必要的套件是否可以正常導入"""
    print("🧪 測試套件導入...")
    
    tests = [
        ("langchain", "LangChain"),
        ("langchain_community", "LangChain Community"),
        ("langchain_openai", "LangChain OpenAI"),
        ("chromadb", "ChromaDB"),
        ("pypdf", "PyPDF"),
        ("docx", "python-docx"),
        ("markdown", "Markdown"),
        ("bs4", "BeautifulSoup4"),
        ("dotenv", "python-dotenv"),
        ("openai", "OpenAI"),
        ("tiktoken", "tiktoken"),
    ]
    
    failed = []
    
    for module, name in tests:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError as e:
            print(f"  ✗ {name} - {e}")
            failed.append(name)
    
    return failed


def test_project_structure():
    """測試專案結構是否正確"""
    print("\n📁 測試專案結構...")
    
    import os
    from pathlib import Path
    
    required_files = [
        "main.py",
        "requirements.txt",
        ".env.example",
        "README.md",
        "knowledge_base/__init__.py",
        "knowledge_base/agent.py",
        "knowledge_base/vector_store.py",
        "knowledge_base/document_processor.py",
        "knowledge_base/tools/__init__.py",
        "knowledge_base/tools/knowledge_tools.py",
    ]
    
    required_dirs = [
        "knowledge_base",
        "knowledge_base/tools",
        "knowledge_base/data",
        "knowledge_base/documents",
    ]
    
    missing = []
    
    for file in required_files:
        if Path(file).exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} (缺少)")
            missing.append(file)
    
    for dir in required_dirs:
        if Path(dir).is_dir():
            print(f"  ✓ {dir}/")
        else:
            print(f"  ✗ {dir}/ (缺少)")
            missing.append(dir)
    
    return missing


def test_env_file():
    """測試環境變數檔案"""
    print("\n🔧 測試環境變數...")
    
    import os
    from pathlib import Path
    
    if Path(".env").exists():
        print("  ✓ .env 檔案存在")
        
        from dotenv import load_dotenv
        load_dotenv()
        
        if os.getenv("OPENAI_API_KEY"):
            print("  ✓ OPENAI_API_KEY 已設定")
            return True
        else:
            print("  ⚠ OPENAI_API_KEY 未設定")
            return False
    else:
        print("  ⚠ .env 檔案不存在（請從 .env.example 複製）")
        return False


def main():
    """主函數"""
    print("=" * 60)
    print("個人智識庫 AI Agent - 安裝測試".center(60))
    print("=" * 60)
    
    # 測試導入
    failed_imports = test_imports()
    
    # 測試專案結構
    missing_files = test_project_structure()
    
    # 測試環境變數
    env_ok = test_env_file()
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結".center(60))
    print("=" * 60)
    
    if failed_imports:
        print(f"\n❌ 有 {len(failed_imports)} 個套件導入失敗:")
        for pkg in failed_imports:
            print(f"   - {pkg}")
        print("\n請執行: pip install -r requirements.txt")
    else:
        print("\n✅ 所有套件導入成功")
    
    if missing_files:
        print(f"\n❌ 有 {len(missing_files)} 個檔案/目錄缺少:")
        for file in missing_files:
            print(f"   - {file}")
    else:
        print("✅ 專案結構完整")
    
    if not env_ok:
        print("\n⚠️  請設定 .env 檔案和 OPENAI_API_KEY")
    else:
        print("✅ 環境變數設定完成")
    
    if not failed_imports and not missing_files and env_ok:
        print("\n" + "=" * 60)
        print("🎉 安裝測試全部通過！可以開始使用了！".center(60))
        print("=" * 60)
        print("\n執行 'python main.py' 啟動應用程式")
        return 0
    else:
        print("\n" + "=" * 60)
        print("⚠️  請修復上述問題後再試".center(60))
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

