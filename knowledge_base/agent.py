"""AI Agent 核心模組"""

import os
from typing import List
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from langchain_classic.memory import ConversationBufferMemory

from knowledge_base.tools.knowledge_tools import (
    KnowledgeSearchTool,
    DocumentSummaryTool
)
from knowledge_base.tools.stock_tools import (
    StockPriceTool,
    TechnicalAnalysisTool,
    MarketSummaryTool,
    StockChartTool,
    TradingSignalTool,
    StockPredictionTool
)


class KnowledgeAgent:
    """個人智識庫 AI Agent"""

    def __init__(
        self,
        vector_store,
        model_name: str = "grok-beta",
        temperature: float = 0.7,
        max_iterations: int = 10,
        verbose: bool = True
    ):
        """
        初始化 AI Agent

        Args:
            vector_store: 向量資料庫實例
            model_name: xAI 模型名稱
            temperature: 溫度參數
            max_iterations: 最大迭代次數
            verbose: 是否顯示詳細資訊
        """
        self.vector_store = vector_store

        # 使用 xAI (Grok) API
        xai_api_key = os.getenv("XAI_API_KEY")
        xai_base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")

        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=xai_api_key,
            openai_api_base=xai_base_url
        )

        self.max_iterations = max_iterations
        self.verbose = verbose
        
        # 初始化記憶
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # 建立工具
        self.tools = self._create_tools()
        
        # 建立 Agent
        self.agent_executor = self._create_agent()
    
    def _create_tools(self) -> List[BaseTool]:
        """建立 Agent 工具"""
        tools = []

        # 智識庫搜尋工具
        search_tool = KnowledgeSearchTool()
        search_tool.vector_store = self.vector_store
        tools.append(search_tool)

        # 文件摘要工具
        summary_tool = DocumentSummaryTool()
        summary_tool.vector_store = self.vector_store
        summary_tool.llm = self.llm
        tools.append(summary_tool)

        # 股票分析工具
        stock_price_tool = StockPriceTool()
        tools.append(stock_price_tool)

        technical_analysis_tool = TechnicalAnalysisTool()
        tools.append(technical_analysis_tool)

        market_summary_tool = MarketSummaryTool()
        tools.append(market_summary_tool)

        # 股票圖表和交易訊號工具
        stock_chart_tool = StockChartTool()
        tools.append(stock_chart_tool)

        trading_signal_tool = TradingSignalTool()
        tools.append(trading_signal_tool)

        # 股票走勢預測工具
        prediction_tool = StockPredictionTool()
        tools.append(prediction_tool)

        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """建立 Agent 執行器"""
        # ReAct 提示模板 (create_react_agent 會自動注入 {tools} 和 {tool_names})
        react_template = """你是一個個人智識庫助手，專門幫助用戶管理和查詢他們的知識庫，同時具備台灣股票分析能力。

你可以使用以下工具：

{tools}

使用以下格式：

Question: 用戶的問題
Thought: 思考應該做什麼
Action: 要使用的工具名稱，必須是 [{tool_names}] 之一
Action Input: 工具的輸入參數（JSON格式）
Observation: 工具返回的結果
... (可以重複 Thought/Action/Action Input/Observation 多次)
Thought: 我現在知道最終答案了
Final Answer: 給用戶的最終回答

重要提示：
- 當用戶要求生成圖表時，必須使用 stock_chart 工具
- 當用戶要求預測走勢時，必須使用 stock_prediction 工具
- 台灣股票代碼為4位數字，例如 2330（台積電）、2344（華邦電）
- 請用繁體中文回答

開始！

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate(
            template=react_template,
            input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
        )

        # 建立 ReAct Agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        # 建立 Agent 執行器
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            max_iterations=self.max_iterations,
            verbose=self.verbose,
            handle_parsing_errors=True
        )

        return agent_executor
    
    def query(self, question: str) -> str:
        """
        向 Agent 提問
        
        Args:
            question: 問題
            
        Returns:
            回答
        """
        try:
            response = self.agent_executor.invoke({"input": question})
            return response.get("output", "無法生成回答")
        except Exception as e:
            return f"處理問題時發生錯誤: {str(e)}"
    
    def clear_memory(self):
        """清除對話記憶"""
        self.memory.clear()
        print("✓ 已清除對話記憶")

