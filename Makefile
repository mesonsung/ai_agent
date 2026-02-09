.PHONY: help install test run example clean setup

help:
	@echo "個人智識庫 AI Agent - 可用指令"
	@echo "================================"
	@echo "make setup      - 完整安裝（建立虛擬環境、安裝依賴）"
	@echo "make install    - 安裝依賴套件"
	@echo "make test       - 測試安裝是否成功"
	@echo "make run        - 啟動應用程式"
	@echo "make example    - 執行使用範例"
	@echo "make clean      - 清理快取和資料"
	@echo "make clean-all  - 清理所有（包含虛擬環境）"
	@echo "================================"

setup:
	@echo "🚀 開始完整安裝..."
	bash setup.sh

install:
	@echo "📥 安裝依賴套件..."
	pip install --upgrade pip
	pip install -r requirements.txt

test:
	@echo "🧪 測試安裝..."
	python test_installation.py

run:
	@echo "🚀 啟動應用程式..."
	python main.py

example:
	@echo "📚 執行使用範例..."
	python example_usage.py

clean:
	@echo "🧹 清理快取和資料..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf knowledge_base/data/chroma/* 2>/dev/null || true
	@echo "✓ 清理完成"

clean-all: clean
	@echo "🧹 清理所有（包含虛擬環境）..."
	rm -rf venv
	@echo "✓ 完全清理完成"

