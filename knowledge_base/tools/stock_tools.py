"""股票分析工具 - 使用 TWSE 台灣證券交易所數據"""

from typing import Optional, Type, Any
from langchain_core.tools import BaseTool
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel, Field, ConfigDict

from .twse_data import TWSEDataFetcher
from .stock_chart import StockChartGenerator


class StockPriceInput(BaseModel):
    """股票價格查詢工具的輸入模型"""
    stock_id: str = Field(description="台灣股票代碼，例如 2330（台積電）、2317（鴻海）")


class StockPriceTool(BaseTool):
    """股票即時價格查詢工具"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "stock_price"
    description: str = """
    查詢台灣股票的即時價格和基本資訊。
    輸入股票代碼（例如：2330、2317、2454）即可獲取該股票的最新價格、漲跌幅、成交量等資訊。
    此工具使用台灣證券交易所（TWSE）的數據。
    """
    args_schema: Type[BaseModel] = StockPriceInput
    fetcher: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fetcher = TWSEDataFetcher()
    
    def _run(
        self,
        stock_id: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """執行股票價格查詢"""
        try:
            info = self.fetcher.get_stock_info(stock_id)
            
            if 'error' in info:
                return f"查詢失敗：{info['error']}"
            
            result = f"""
📊 股票資訊 - {info.get('stock_id', stock_id)} {info.get('name', '')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 收盤價：{info.get('close', 'N/A')} 元
📈 漲跌：{info.get('change', 'N/A')}
📉 開盤價：{info.get('open', 'N/A')} 元
⬆️ 最高價：{info.get('high', 'N/A')} 元
⬇️ 最低價：{info.get('low', 'N/A')} 元
📊 成交量：{info.get('trade_volume', 'N/A')} 股
💵 成交金額：{info.get('trade_value', 'N/A')} 元
🔄 成交筆數：{info.get('transaction', 'N/A')} 筆
"""
            return result.strip()
            
        except Exception as e:
            return f"查詢時發生錯誤：{str(e)}"


class TechnicalAnalysisInput(BaseModel):
    """技術分析工具的輸入模型"""
    stock_id: str = Field(description="台灣股票代碼，例如 2330（台積電）")


class TechnicalAnalysisTool(BaseTool):
    """股票技術分析工具"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "technical_analysis"
    description: str = """
    對台灣股票進行技術分析，計算並解讀多種技術指標。
    包括：移動平均線(MA5/10/20)、RSI、KD、MACD、布林通道等。
    會根據技術指標給出多空訊號解讀。
    輸入股票代碼即可獲取完整的技術分析報告。
    """
    args_schema: Type[BaseModel] = TechnicalAnalysisInput
    fetcher: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fetcher = TWSEDataFetcher()
    
    def _run(
        self,
        stock_id: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """執行技術分析"""
        try:
            analysis = self.fetcher.analyze_stock(stock_id)
            
            if 'error' in analysis and 'info' not in analysis:
                return f"分析失敗：{analysis['error']}"
            
            result = f"""
📈 技術分析報告 - {analysis.get('stock_id', stock_id)} {analysis.get('name', '')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 當前價格：{analysis.get('current_price', 'N/A')} 元
📉 漲跌：{analysis.get('change', 'N/A')}
📊 成交量：{analysis.get('volume', 'N/A')} 股
"""
            
            # 技術指標
            tech = analysis.get('technical', {})
            if tech:
                result += f"""
🔧 技術指標
──────────────────────────
📏 均線指標：
   • MA5：{tech.get('MA5', 'N/A')}
   • MA10：{tech.get('MA10', 'N/A')}
   • MA20：{tech.get('MA20', 'N/A')}

📊 動能指標：
   • RSI(14)：{tech.get('RSI', 'N/A')}
   • K 值：{tech.get('K', 'N/A')}
   • D 值：{tech.get('D', 'N/A')}

📈 趨勢指標：
   • MACD：{tech.get('MACD', 'N/A')}
   • Signal：{tech.get('MACD_Signal', 'N/A')}
"""
            
            # 訊號解讀
            signals = analysis.get('signals', [])
            if signals:
                result += "\n💡 訊號解讀\n──────────────────────────\n"
                for signal in signals:
                    result += f"   • {signal}\n"
            
            return result.strip()
            
        except Exception as e:
            return f"分析時發生錯誤：{str(e)}"


class MarketSummaryInput(BaseModel):
    """大盤資訊工具的輸入模型"""
    pass


class MarketSummaryTool(BaseTool):
    """大盤指數查詢工具"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "market_summary"
    description: str = """
    查詢台灣加權指數（大盤）的最新資訊。
    包括指數點數、漲跌幅、成交量、成交金額等。
    不需要輸入任何參數。
    """
    args_schema: Type[BaseModel] = MarketSummaryInput
    fetcher: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fetcher = TWSEDataFetcher()
    
    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """執行大盤查詢"""
        try:
            summary = self.fetcher.get_market_summary()
            
            if 'error' in summary:
                return f"查詢失敗：{summary['error']}"
            
            result = f"""
🏛️ 台灣加權指數
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 日期：{summary.get('date', 'N/A')}
📈 指數：{summary.get('index', 'N/A')} 點
📊 漲跌：{summary.get('change', 'N/A')} 點
📊 成交股數：{summary.get('volume', 'N/A')}
💵 成交金額：{summary.get('value', 'N/A')}
🔄 成交筆數：{summary.get('transaction', 'N/A')}
"""
            return result.strip()

        except Exception as e:
            return f"查詢時發生錯誤：{str(e)}"


class StockChartInput(BaseModel):
    """股票圖表工具的輸入模型"""
    stock_id: str = Field(description="台灣股票代碼，例如 2330（台積電）")
    months: int = Field(default=3, description="獲取幾個月的歷史數據，預設3個月")


class StockChartTool(BaseTool):
    """股票圖表生成工具"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "stock_chart"
    description: str = """生成台灣股票的技術分析圖表。

    參數：
    - stock_id: 股票代碼（如 2330, 2344）
    - months: 歷史數據月數（預設3）

    輸入範例：2330 或 2344
    """
    args_schema: Type[BaseModel] = StockChartInput
    fetcher: Any = None
    chart_generator: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fetcher = TWSEDataFetcher()
        self.chart_generator = StockChartGenerator(show_chart=True)

    def _run(
        self,
        stock_id: str = None,
        months: int = 3,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs
    ) -> str:
        """執行圖表生成"""
        import json
        import re

        try:
            # 處理多種輸入格式
            if stock_id is None:
                stock_id = kwargs.get('stock_code') or kwargs.get('code') or kwargs.get('id')

            # 如果 stock_id 是 JSON 字串，嘗試解析
            if stock_id and isinstance(stock_id, str):
                stock_id = stock_id.strip()
                if stock_id.startswith('{'):
                    try:
                        parsed = json.loads(stock_id)
                        stock_id = parsed.get('stock_id') or parsed.get('stock_code') or parsed.get('code')
                        months = parsed.get('months', months)
                    except:
                        pass
                # 提取純數字股票代碼
                match = re.search(r'(\d{4})', str(stock_id))
                if match:
                    stock_id = match.group(1)

            if not stock_id:
                return "錯誤：請提供股票代碼 (stock_id)"

            # 獲取股票資訊
            info = self.fetcher.get_stock_info(stock_id)
            stock_name = info.get('name', '')

            # 獲取歷史數據
            df = self.fetcher.get_stock_history(stock_id, months=months)

            if df.empty:
                return f"無法獲取 {stock_id} 的歷史數據"

            # 計算技術指標
            df = self.fetcher.calculate_technical_indicators(df)

            # 計算支撐壓力位
            sr = self.fetcher.calculate_support_resistance(df)

            # 生成交易訊號
            signals = self.fetcher.generate_trading_signals(df)

            # 找出買賣點
            points = self.fetcher.find_buy_sell_points(df)

            # 生成圖表
            chart_path = self.chart_generator.generate_price_chart(
                df=df,
                stock_id=stock_id,
                stock_name=stock_name,
                buy_points=points.get('buy_points', []),
                sell_points=points.get('sell_points', []),
                support_levels=sr.get('support', []),
                resistance_levels=sr.get('resistance', [])
            )

            # 生成分析報告
            summary = self.chart_generator.generate_summary_text(
                stock_id=stock_id,
                stock_name=stock_name,
                trading_signals=signals,
                support_resistance=sr
            )

            result = f"""
📊 股票技術分析圖表已生成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{summary}

📁 圖表檔案: {chart_path}

📈 歷史買賣點統計:
   買入點: {len(points.get('buy_points', []))} 個
   賣出點: {len(points.get('sell_points', []))} 個
"""
            return result.strip()

        except Exception as e:
            return f"生成圖表時發生錯誤：{str(e)}"


class TradingSignalInput(BaseModel):
    """交易訊號工具的輸入模型"""
    stock_id: str = Field(description="台灣股票代碼，例如 2330（台積電）")


class TradingSignalTool(BaseTool):
    """交易訊號建議工具"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "trading_signal"
    description: str = """
    分析台灣股票並提供交易建議和買賣訊號。
    基於多種技術指標（MA、RSI、KD、MACD、布林通道）綜合判斷，
    給出強烈買入、買入、觀望、賣出、強烈賣出等建議。
    同時計算支撐位和壓力位，提供操作參考價位。
    """
    args_schema: Type[BaseModel] = TradingSignalInput
    fetcher: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fetcher = TWSEDataFetcher()

    def _run(
        self,
        stock_id: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """執行交易訊號分析"""
        try:
            # 獲取股票資訊
            info = self.fetcher.get_stock_info(stock_id)
            stock_name = info.get('name', '')
            current_price = info.get('close', 'N/A')

            # 獲取歷史數據並計算指標
            df = self.fetcher.get_stock_history(stock_id, months=3)

            if df.empty:
                return f"無法獲取 {stock_id} 的歷史數據"

            df = self.fetcher.calculate_technical_indicators(df)

            # 計算支撐壓力位
            sr = self.fetcher.calculate_support_resistance(df)

            # 生成交易訊號
            signals = self.fetcher.generate_trading_signals(df)

            # 建立結果
            action_emoji = {
                'STRONG_BUY': '🔥 強烈買入',
                'BUY': '📈 買入',
                'HOLD': '⏸️ 觀望',
                'SELL': '📉 賣出',
                'STRONG_SELL': '⚠️ 強烈賣出'
            }

            action = signals.get('action', 'HOLD')

            result = f"""
💹 交易訊號分析 - {stock_id} {stock_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 當前價格: {current_price}

🎯 交易建議: {action_emoji.get(action, signals.get('recommendation', '觀望'))}
   買入分數: {signals.get('buy_score', 0)} 分
   賣出分數: {signals.get('sell_score', 0)} 分
   綜合分數: {signals.get('total_score', 0)} 分
"""

            # 訊號列表
            sig_list = signals.get('signals', [])
            if sig_list:
                result += "\n📋 技術指標訊號:\n"
                for sig in sig_list:
                    sig_icon = '🟢' if sig['type'] == 'BUY' else '🔴'
                    result += f"   {sig_icon} [{sig['indicator']}] {sig['reason']} (強度: {sig['strength']})\n"

            # 支撐壓力位
            support = sr.get('support', [])
            resistance = sr.get('resistance', [])

            if resistance:
                result += "\n⬆️ 壓力位:\n"
                for r in resistance[:3]:
                    result += f"   📍 {r:.2f}\n"

            if support:
                result += "\n⬇️ 支撐位:\n"
                for s in support[:3]:
                    result += f"   📍 {s:.2f}\n"

            return result.strip()

        except Exception as e:
            return f"分析時發生錯誤：{str(e)}"


class PredictionInput(BaseModel):
    """股票走勢預測工具的輸入模型"""
    stock_id: str = Field(description="台灣股票代碼，例如 2330（台積電）、2317（鴻海）")
    days: int = Field(default=5, description="預測天數，預設為 5 天，最多 10 天")


class StockPredictionTool(BaseTool):
    """股票走勢預測工具"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "stock_prediction"
    description: str = """
    預測台灣股票未來走勢。
    使用技術分析（RSI、KD、MACD、均線等）和統計方法預測未來價格走勢。
    輸入股票代碼和預測天數，獲取：
    - 趨勢判斷（強勢上漲/偏多/盤整/偏空/強勢下跌）
    - 預測價格和信賴區間
    - 目標價和停損價
    - 支撐位和壓力位
    此工具使用台灣證券交易所（TWSE）的數據。
    """
    args_schema: Type[BaseModel] = PredictionInput
    fetcher: Any = None
    chart_generator: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fetcher = TWSEDataFetcher()
        self.chart_generator = StockChartGenerator(show_chart=True)

    def _run(
        self,
        stock_id: str = None,
        days: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs
    ) -> str:
        """執行股票走勢預測"""
        import json
        import re

        try:
            # 處理多種輸入格式
            if stock_id is None:
                stock_id = kwargs.get('stock_code') or kwargs.get('code') or kwargs.get('id')

            # 如果 stock_id 是 JSON 字串，嘗試解析
            if stock_id and isinstance(stock_id, str):
                stock_id = stock_id.strip()
                if stock_id.startswith('{'):
                    try:
                        parsed = json.loads(stock_id)
                        stock_id = parsed.get('stock_id') or parsed.get('stock_code') or parsed.get('code')
                        days = parsed.get('days', days)
                    except:
                        pass
                # 提取純數字股票代碼
                match = re.search(r'(\d{4})', str(stock_id))
                if match:
                    stock_id = match.group(1)

            if not stock_id:
                return "錯誤：請提供股票代碼 (stock_id)"

            # 限制預測天數
            days = min(max(days, 1), 10)

            # 獲取股票資訊
            info = self.fetcher.get_stock_info(stock_id)
            stock_name = info.get('name', '')

            # 獲取歷史數據
            df = self.fetcher.get_stock_history(stock_id, months=3)
            if df.empty:
                return f"無法獲取 {stock_id} 的歷史數據"

            # 計算技術指標
            df = self.fetcher.calculate_technical_indicators(df)

            # 預測走勢
            prediction = self.fetcher.predict_future_trend(df, days=days)

            if 'error' in prediction:
                return f"預測失敗：{prediction['error']}"

            # 生成預測圖表
            chart_path = self.chart_generator.generate_prediction_chart(
                df=df,
                predictions=prediction,
                stock_id=stock_id,
                stock_name=stock_name
            )

            # 趨勢表情符號
            trend_emoji = {
                'STRONG_UP': '🚀',
                'UP': '📈',
                'NEUTRAL': '➡️',
                'DOWN': '📉',
                'STRONG_DOWN': '⚠️'
            }

            trend = prediction.get('trend', 'NEUTRAL')

            result = f"""
🔮 走勢預測 - {stock_id} {stock_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 當前價格: {prediction['current_price']:.2f} 元
{trend_emoji.get(trend, '📊')} 趨勢判斷: {prediction['trend_description']}
📊 趨勢分數: {prediction['trend_score']:+d} 分
📈 年化波動率: {prediction['volatility']:.1f}%

🎯 目標價: {prediction.get('target_price', 'N/A')} 元
⛔ 停損價: {prediction.get('stop_loss', 'N/A')} 元
"""

            # 趨勢因素
            factors = prediction.get('trend_factors', [])
            if factors:
                result += "\n📋 趨勢分析因素:\n"
                for factor in factors:
                    result += f"   • {factor}\n"

            # 預測價格表
            preds = prediction.get('predictions', [])
            if preds:
                result += "\n📅 未來走勢預測:\n"
                result += "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                for p in preds:
                    change_icon = '📈' if p['change_pct'] > 0 else '📉' if p['change_pct'] < 0 else '➡️'
                    result += f"   第{p['day']}天: {p['predicted_price']:.2f} ({p['change_pct']:+.2f}%) {change_icon}\n"
                    result += f"         信賴區間: {p['lower_bound']:.2f} ~ {p['upper_bound']:.2f}\n"

            # 支撐壓力位
            support = prediction.get('support_levels', [])
            resistance = prediction.get('resistance_levels', [])

            if resistance:
                result += "\n⬆️ 壓力位: " + ", ".join([f"{r:.2f}" for r in resistance[:3]]) + "\n"
            if support:
                result += "⬇️ 支撐位: " + ", ".join([f"{s:.2f}" for s in support[:3]]) + "\n"

            if chart_path:
                result += f"\n📊 預測圖表已生成: {chart_path}\n"

            return result.strip()

        except Exception as e:
            return f"預測時發生錯誤：{str(e)}"
