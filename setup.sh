#!/bin/bash

echo "🚀 個人智識庫 AI Agent 安裝腳本"
echo "================================"

# 檢查 Python 版本
echo "📌 檢查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python 版本: $python_version"

# 建立虛擬環境
echo ""
echo "📦 建立虛擬環境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ 虛擬環境建立完成"
else
    echo "✓ 虛擬環境已存在"
fi

# 啟動虛擬環境
echo ""
echo "🔧 啟動虛擬環境..."
source venv/bin/activate

# 安裝依賴
echo ""
echo "📥 安裝依賴套件..."
pip install --upgrade pip
pip install -r requirements.txt

# 建立 .env 檔案
echo ""
if [ ! -f ".env" ]; then
    echo "📝 建立 .env 檔案..."
    cp .env.example .env
    echo "✓ .env 檔案已建立，請編輯此檔案並填入您的 OPENAI_API_KEY"
else
    echo "✓ .env 檔案已存在"
fi

# 建立必要的目錄
echo ""
echo "📁 建立必要的目錄..."
mkdir -p knowledge_base/data/chroma
mkdir -p knowledge_base/documents
echo "✓ 目錄建立完成"

echo ""
echo "================================"
echo "✅ 安裝完成！"
echo ""
echo "下一步："
echo "1. 編輯 .env 檔案，填入您的 OPENAI_API_KEY"
echo "2. 執行 'source venv/bin/activate' 啟動虛擬環境"
echo "3. 執行 'python main.py' 啟動應用程式"
echo ""

