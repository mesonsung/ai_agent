# 快速開始指南

## 5 分鐘快速上手

### 1️⃣ 安裝依賴

```bash
# 執行自動安裝腳本
bash setup.sh

# 或手動安裝
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ 設定 API 金鑰

```bash
# 複製環境變數範本
cp .env.example .env

# 編輯 .env 檔案，填入您的 OpenAI API 金鑰
# OPENAI_API_KEY=sk-your-api-key-here
```

### 3️⃣ 測試安裝

```bash
python test_installation.py
```

### 4️⃣ 啟動應用程式

```bash
python main.py
```

## 基本使用

### 新增文件到智識庫

```
👤 請輸入指令: add ./knowledge_base/documents/example.txt
```

或新增整個目錄：

```
👤 請輸入指令: add ./knowledge_base/documents/
```

### 向智識庫提問

方法 1 - 使用 query 指令：
```
👤 請輸入指令: query
💭 請輸入您的問題: 什麼是機器學習？
```

方法 2 - 直接輸入問題：
```
👤 請輸入指令: 深度學習和機器學習有什麼區別？
```

### 其他指令

```bash
clear    # 清除對話記憶
formats  # 顯示支援的文件格式
help     # 顯示幫助選單
exit     # 退出程式
```

## 程式化使用

查看 `example_usage.py` 了解如何在 Python 程式中使用智識庫：

```bash
python example_usage.py
```

## 支援的文件格式

- `.txt` - 純文字檔案
- `.pdf` - PDF 文件
- `.docx` - Word 文件
- `.md` - Markdown 文件

## 常見問題

### Q: 如何獲取 OpenAI API 金鑰？

A: 訪問 https://platform.openai.com/api-keys 註冊並建立 API 金鑰。

### Q: 可以使用其他 LLM 嗎？

A: 可以！修改 `knowledge_base/agent.py` 中的 `ChatOpenAI` 為其他 LangChain 支援的 LLM。

### Q: 如何清空智識庫？

A: 刪除 `knowledge_base/data/chroma/` 目錄即可。

### Q: 文件會被分割嗎？

A: 是的，文件會被分割成約 1000 字元的片段，重疊 200 字元，以提高搜尋效率。

### Q: 可以新增多少文件？

A: 理論上沒有限制，但建議定期清理不需要的文件以提高效能。

## 進階配置

編輯 `.env` 檔案可以調整以下參數：

```env
# 使用的模型
OPENAI_MODEL=gpt-4-turbo-preview

# 嵌入模型
EMBEDDING_MODEL=text-embedding-3-small

# Agent 最大迭代次數
MAX_ITERATIONS=10

# 是否顯示詳細資訊
VERBOSE=true
```

## 專案結構

```
ai_agent/
├── main.py                    # 主程式
├── example_usage.py           # 使用範例
├── test_installation.py       # 安裝測試
├── setup.sh                   # 安裝腳本
├── requirements.txt           # Python 依賴
├── .env.example              # 環境變數範本
├── README.md                 # 完整文件
├── QUICKSTART.md            # 本檔案
└── knowledge_base/
    ├── __init__.py
    ├── agent.py              # AI Agent 核心
    ├── vector_store.py       # 向量資料庫
    ├── document_processor.py # 文件處理
    ├── tools/                # Agent 工具
    ├── data/                 # 資料儲存
    └── documents/            # 文件目錄
```

## 下一步

1. 將您的文件放入 `knowledge_base/documents/` 目錄
2. 使用 `add` 指令新增文件到智識庫
3. 開始提問！

需要更多幫助？查看 `README.md` 獲取完整文件。

