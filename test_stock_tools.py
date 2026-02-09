#!/usr/bin/env python3
"""測試股票分析工具"""

import sys


def test_twse_data_fetcher():
    """測試 TWSE 數據獲取器"""
    print("\n" + "=" * 50)
    print("測試 TWSE 數據獲取器")
    print("=" * 50)
    
    try:
        from knowledge_base.tools.twse_data import TWSEDataFetcher
        print("✓ 成功匯入 TWSEDataFetcher")
        
        fetcher = TWSEDataFetcher()
        print("✓ 成功建立 TWSEDataFetcher 實例")
        
        # 測試獲取股票資訊 (台積電 2330)
        print("\n測試獲取股票資訊 (2330 台積電)...")
        info = fetcher.get_stock_info("2330")
        if 'error' not in info:
            print(f"✓ 股票代碼: {info.get('stock_id', 'N/A')}")
            print(f"  名稱: {info.get('name', 'N/A')}")
            print(f"  收盤價: {info.get('close', 'N/A')}")
            print(f"  漲跌: {info.get('change', 'N/A')}")
        else:
            print(f"✗ 獲取失敗: {info['error']}")
        
        # 測試獲取歷史數據
        print("\n測試獲取歷史數據...")
        history = fetcher.get_stock_history("2330", months=1)
        if not history.empty:
            print(f"✓ 獲取到 {len(history)} 筆歷史數據")
            print(f"  日期範圍: {history['date'].iloc[0]} ~ {history['date'].iloc[-1]}")
        else:
            print("✗ 無法獲取歷史數據")
        
        # 測試技術指標計算
        print("\n測試技術指標計算...")
        if not history.empty and len(history) >= 20:
            history_with_indicators = fetcher.calculate_technical_indicators(history)
            print(f"✓ 成功計算技術指標")
            latest = history_with_indicators.iloc[-1]
            print(f"  最新收盤價: {latest.get('close', 'N/A')}")
            print(f"  MA5: {latest.get('MA5', 'N/A'):.2f}" if latest.get('MA5') else "  MA5: N/A")
            print(f"  RSI: {latest.get('RSI', 'N/A'):.2f}" if latest.get('RSI') else "  RSI: N/A")
        else:
            print("△ 歷史數據不足，跳過技術指標測試")
        
        # 測試綜合分析
        print("\n測試綜合分析...")
        analysis = fetcher.analyze_stock("2330")
        if 'error' not in analysis or 'info' in analysis:
            print("✓ 成功進行綜合分析")
            if 'signals' in analysis:
                print("  訊號解讀:")
                for signal in analysis.get('signals', [])[:3]:
                    print(f"    • {signal}")
        else:
            print(f"✗ 分析失敗: {analysis.get('error', 'Unknown error')}")
        
        return True
        
    except ImportError as e:
        print(f"✗ 匯入失敗: {e}")
        return False
    except Exception as e:
        print(f"✗ 測試失敗: {e}")
        return False


def test_stock_tools():
    """測試 LangChain 股票工具"""
    print("\n" + "=" * 50)
    print("測試 LangChain 股票工具")
    print("=" * 50)
    
    try:
        from knowledge_base.tools.stock_tools import (
            StockPriceTool,
            TechnicalAnalysisTool,
            MarketSummaryTool
        )
        print("✓ 成功匯入股票工具")
        
        # 測試股票價格工具
        print("\n測試 StockPriceTool...")
        price_tool = StockPriceTool()
        result = price_tool._run("2330")
        if "錯誤" not in result and "失敗" not in result:
            print("✓ StockPriceTool 運作正常")
            print(result[:200] + "..." if len(result) > 200 else result)
        else:
            print(f"△ StockPriceTool: {result}")
        
        # 測試技術分析工具
        print("\n測試 TechnicalAnalysisTool...")
        tech_tool = TechnicalAnalysisTool()
        result = tech_tool._run("2330")
        if "錯誤" not in result and "失敗" not in result:
            print("✓ TechnicalAnalysisTool 運作正常")
        else:
            print(f"△ TechnicalAnalysisTool: {result[:100]}...")
        
        # 測試大盤工具
        print("\n測試 MarketSummaryTool...")
        market_tool = MarketSummaryTool()
        result = market_tool._run()
        if "錯誤" not in result and "失敗" not in result:
            print("✓ MarketSummaryTool 運作正常")
            print(result)
        else:
            print(f"△ MarketSummaryTool: {result}")
        
        return True
        
    except ImportError as e:
        print(f"✗ 匯入失敗: {e}")
        return False
    except Exception as e:
        print(f"✗ 測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("=" * 50)
    print("股票分析工具測試")
    print("=" * 50)
    
    results = []
    
    # 測試 TWSE 數據獲取器
    results.append(("TWSE 數據獲取器", test_twse_data_fetcher()))
    
    # 測試 LangChain 工具
    results.append(("LangChain 股票工具", test_stock_tools()))
    
    # 顯示結果摘要
    print("\n" + "=" * 50)
    print("測試結果摘要")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✓ 通過" if passed else "✗ 失敗"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

