"""TWSE 台灣證券交易所數據獲取模組"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import time
import json


class TWSEDataFetcher:
    """台灣證券交易所數據獲取器"""
    
    BASE_URL = "https://www.twse.com.tw"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        })
    
    def get_stock_info(self, stock_id: str) -> Dict[str, Any]:
        """
        獲取股票基本資訊

        Args:
            stock_id: 股票代碼，例如 "2330"

        Returns:
            股票基本資訊字典
        """
        # 直接使用個股日成交資訊 API，更穩定
        return self._get_stock_info_alternative(stock_id)
    
    def _get_stock_info_alternative(self, stock_id: str) -> Dict[str, Any]:
        """備用方案獲取股票資訊"""
        try:
            today = datetime.now()
            date_str = today.strftime("%Y%m%d")
            url = f"{self.BASE_URL}/exchangeReport/STOCK_DAY?response=json&date={date_str}&stockNo={stock_id}"

            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('stat') == 'OK' and 'data' in data and len(data['data']) > 0:
                    latest = data['data'][-1]
                    # 從 title 提取股票名稱: "115年02月 2330 台積電           各日成交資訊"
                    title = data.get('title', '')
                    name = ''
                    if title:
                        parts = title.split()
                        if len(parts) >= 3:
                            name = parts[2]  # 取得股票名稱

                    return {
                        'stock_id': stock_id,
                        'name': name,
                        'date': latest[0],
                        'trade_volume': latest[1],
                        'trade_value': latest[2],
                        'open': latest[3],
                        'high': latest[4],
                        'low': latest[5],
                        'close': latest[6],
                        'change': latest[7],
                        'transaction': latest[8]
                    }
            return {'error': '無法獲取股票資訊'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_stock_history(self, stock_id: str, months: int = 3) -> pd.DataFrame:
        """
        獲取股票歷史數據
        
        Args:
            stock_id: 股票代碼
            months: 獲取幾個月的數據
            
        Returns:
            DataFrame 包含歷史價格數據
        """
        all_data = []
        
        for i in range(months):
            date = datetime.now() - timedelta(days=30 * i)
            date_str = date.strftime("%Y%m%d")
            
            try:
                url = f"{self.BASE_URL}/exchangeReport/STOCK_DAY?response=json&date={date_str}&stockNo={stock_id}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data:
                        all_data.extend(data['data'])
                
                time.sleep(0.5)  # 避免請求過快
                
            except Exception:
                continue
        
        if not all_data:
            return pd.DataFrame()

        # API 返回 10 個欄位：日期, 成交股數, 成交金額, 開盤價, 最高價, 最低價, 收盤價, 漲跌價差, 成交筆數, 註記
        columns = ['date', 'volume', 'value', 'open', 'high', 'low', 'close', 'change', 'transaction', 'note']

        # 轉換為 DataFrame
        df = pd.DataFrame(all_data, columns=columns)

        # 移除註記欄位
        df = df.drop(columns=['note'], errors='ignore')

        # 數據清洗
        df = self._clean_data(df)

        return df.drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗數據"""
        df = df.copy()
        
        # 移除逗號並轉換數值
        numeric_cols = ['volume', 'value', 'open', 'high', 'low', 'close', 'transaction']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '').str.replace('--', '0')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 處理漲跌
        if 'change' in df.columns:
            df['change'] = df['change'].astype(str).str.replace(',', '')
            df['change'] = df['change'].apply(self._parse_change)
        
        return df
    
    def _parse_change(self, value: str) -> float:
        """解析漲跌值"""
        try:
            value = str(value).strip()
            if value.startswith('+'):
                return float(value[1:])
            elif value.startswith('-'):
                return -float(value[1:])
            elif value.startswith('X'):
                return 0.0
            else:
                return float(value) if value else 0.0
        except:
            return 0.0

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算技術指標

        Args:
            df: 包含 OHLCV 數據的 DataFrame

        Returns:
            添加了技術指標的 DataFrame
        """
        if df.empty or len(df) < 20:
            return df

        df = df.copy()

        # 移動平均線 (MA)
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA60'] = df['close'].rolling(window=60).mean() if len(df) >= 60 else None

        # RSI (相對強弱指標)
        df['RSI'] = self._calculate_rsi(df['close'], period=14)

        # MACD
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = self._calculate_macd(df['close'])

        # KD 指標
        df['K'], df['D'] = self._calculate_kd(df, period=9)

        # 布林通道
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = self._calculate_bollinger_bands(df['close'])

        return df

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """計算 RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """計算 MACD"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram

    def _calculate_kd(self, df: pd.DataFrame, period: int = 9):
        """計算 KD 指標"""
        low_min = df['low'].rolling(window=period).min()
        high_max = df['high'].rolling(window=period).max()

        rsv = (df['close'] - low_min) / (high_max - low_min) * 100

        k = rsv.ewm(com=2, adjust=False).mean()
        d = k.ewm(com=2, adjust=False).mean()

        return k, d

    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2):
        """計算布林通道"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    def get_market_summary(self) -> Dict[str, Any]:
        """
        獲取大盤指數資訊

        Returns:
            大盤指數資訊
        """
        try:
            url = f"{self.BASE_URL}/exchangeReport/FMTQIK?response=json"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # API 欄位順序：日期, 成交股數, 成交金額, 成交筆數, 發行量加權股價指數, 漲跌點數
                if data.get('stat') == 'OK' and 'data' in data and len(data['data']) > 0:
                    latest = data['data'][-1]
                    return {
                        'date': latest[0],           # 日期
                        'volume': latest[1],         # 成交股數
                        'value': latest[2],          # 成交金額
                        'transaction': latest[3],    # 成交筆數
                        'index': latest[4],          # 發行量加權股價指數
                        'change': latest[5]          # 漲跌點數
                    }
            return {'error': '無法獲取大盤資訊'}
        except Exception as e:
            return {'error': str(e)}

    def analyze_stock(self, stock_id: str) -> Dict[str, Any]:
        """
        綜合分析股票

        Args:
            stock_id: 股票代碼

        Returns:
            綜合分析結果
        """
        # 獲取股票資訊
        info = self.get_stock_info(stock_id)
        if 'error' in info:
            return info

        # 獲取歷史數據並計算技術指標
        history = self.get_stock_history(stock_id, months=3)
        if history.empty:
            return {'error': '無法獲取歷史數據', 'info': info}

        # 計算技術指標
        history = self.calculate_technical_indicators(history)

        # 取得最新數據
        latest = history.iloc[-1] if len(history) > 0 else None

        analysis = {
            'stock_id': stock_id,
            'name': info.get('name', ''),
            'current_price': info.get('close', ''),
            'change': info.get('change', ''),
            'volume': info.get('trade_volume', ''),
        }

        if latest is not None:
            # 技術指標分析
            analysis['technical'] = {
                'MA5': round(latest.get('MA5', 0), 2) if pd.notna(latest.get('MA5')) else None,
                'MA10': round(latest.get('MA10', 0), 2) if pd.notna(latest.get('MA10')) else None,
                'MA20': round(latest.get('MA20', 0), 2) if pd.notna(latest.get('MA20')) else None,
                'RSI': round(latest.get('RSI', 0), 2) if pd.notna(latest.get('RSI')) else None,
                'K': round(latest.get('K', 0), 2) if pd.notna(latest.get('K')) else None,
                'D': round(latest.get('D', 0), 2) if pd.notna(latest.get('D')) else None,
                'MACD': round(latest.get('MACD', 0), 4) if pd.notna(latest.get('MACD')) else None,
                'MACD_Signal': round(latest.get('MACD_Signal', 0), 4) if pd.notna(latest.get('MACD_Signal')) else None,
            }

            # 生成訊號解讀
            analysis['signals'] = self._interpret_signals(latest)

        return analysis

    def _interpret_signals(self, data: pd.Series) -> List[str]:
        """解讀技術指標訊號"""
        signals = []

        # RSI 解讀
        rsi = data.get('RSI')
        if pd.notna(rsi):
            if rsi > 70:
                signals.append("RSI 超買區 (>70)，可能回調")
            elif rsi < 30:
                signals.append("RSI 超賣區 (<30)，可能反彈")
            elif rsi > 50:
                signals.append("RSI 多方區域")
            else:
                signals.append("RSI 空方區域")

        # KD 解讀
        k, d = data.get('K'), data.get('D')
        if pd.notna(k) and pd.notna(d):
            if k > 80 and d > 80:
                signals.append("KD 高檔區，注意回調風險")
            elif k < 20 and d < 20:
                signals.append("KD 低檔區，可能有反彈機會")
            if k > d:
                signals.append("K 線在 D 線上方，短期偏多")
            else:
                signals.append("K 線在 D 線下方，短期偏空")

        # MACD 解讀
        macd, signal = data.get('MACD'), data.get('MACD_Signal')
        if pd.notna(macd) and pd.notna(signal):
            if macd > signal:
                signals.append("MACD 多頭排列")
            else:
                signals.append("MACD 空頭排列")
            if macd > 0:
                signals.append("MACD 在零軸上方，趨勢偏多")
            else:
                signals.append("MACD 在零軸下方，趨勢偏空")

        # 均線解讀
        close = data.get('close')
        ma5, ma10, ma20 = data.get('MA5'), data.get('MA10'), data.get('MA20')
        if pd.notna(close) and pd.notna(ma5) and pd.notna(ma20):
            if close > ma5 > ma20:
                signals.append("股價站上均線，多頭排列")
            elif close < ma5 < ma20:
                signals.append("股價跌破均線，空頭排列")

        return signals

    def calculate_support_resistance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        計算支撐位和壓力位

        Args:
            df: 包含 OHLCV 數據的 DataFrame

        Returns:
            支撐位和壓力位資訊
        """
        if df.empty or len(df) < 5:
            return {'support': [], 'resistance': []}

        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values

        # 找出局部高點和低點
        resistance_levels = []
        support_levels = []

        for i in range(2, len(df) - 2):
            # 局部高點 (壓力位)
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                resistance_levels.append(highs[i])

            # 局部低點 (支撐位)
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                support_levels.append(lows[i])

        # 取最近的支撐壓力位
        current_price = closes[-1]

        # 篩選有效的支撐位 (低於當前價格)
        valid_support = sorted([s for s in support_levels if s < current_price], reverse=True)[:3]

        # 篩選有效的壓力位 (高於當前價格)
        valid_resistance = sorted([r for r in resistance_levels if r > current_price])[:3]

        return {
            'support': valid_support,
            'resistance': valid_resistance,
            'current_price': current_price
        }

    def generate_trading_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成買賣訊號

        Args:
            df: 包含技術指標的 DataFrame

        Returns:
            買賣訊號和建議
        """
        if df.empty or len(df) < 20:
            return {'signals': [], 'recommendation': '數據不足，無法生成訊號'}

        signals = []
        buy_signals = 0
        sell_signals = 0

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else None

        # 1. 均線交叉訊號
        if pd.notna(latest.get('MA5')) and pd.notna(latest.get('MA20')):
            if prev is not None and pd.notna(prev.get('MA5')) and pd.notna(prev.get('MA20')):
                # 黃金交叉
                if prev['MA5'] <= prev['MA20'] and latest['MA5'] > latest['MA20']:
                    signals.append({'type': 'BUY', 'indicator': 'MA', 'reason': 'MA5 上穿 MA20 (黃金交叉)', 'strength': 2})
                    buy_signals += 2
                # 死亡交叉
                elif prev['MA5'] >= prev['MA20'] and latest['MA5'] < latest['MA20']:
                    signals.append({'type': 'SELL', 'indicator': 'MA', 'reason': 'MA5 下穿 MA20 (死亡交叉)', 'strength': 2})
                    sell_signals += 2

        # 2. RSI 訊號
        rsi = latest.get('RSI')
        if pd.notna(rsi):
            if rsi < 30:
                signals.append({'type': 'BUY', 'indicator': 'RSI', 'reason': f'RSI={rsi:.1f} 超賣區', 'strength': 2})
                buy_signals += 2
            elif rsi < 40:
                signals.append({'type': 'BUY', 'indicator': 'RSI', 'reason': f'RSI={rsi:.1f} 接近超賣', 'strength': 1})
                buy_signals += 1
            elif rsi > 70:
                signals.append({'type': 'SELL', 'indicator': 'RSI', 'reason': f'RSI={rsi:.1f} 超買區', 'strength': 2})
                sell_signals += 2
            elif rsi > 60:
                signals.append({'type': 'SELL', 'indicator': 'RSI', 'reason': f'RSI={rsi:.1f} 接近超買', 'strength': 1})
                sell_signals += 1

        # 3. KD 訊號
        k, d = latest.get('K'), latest.get('D')
        if pd.notna(k) and pd.notna(d) and prev is not None:
            prev_k, prev_d = prev.get('K'), prev.get('D')
            if pd.notna(prev_k) and pd.notna(prev_d):
                # KD 黃金交叉 (低檔)
                if k < 30 and prev_k <= prev_d and k > d:
                    signals.append({'type': 'BUY', 'indicator': 'KD', 'reason': f'KD 低檔黃金交叉 (K={k:.1f})', 'strength': 2})
                    buy_signals += 2
                # KD 死亡交叉 (高檔)
                elif k > 70 and prev_k >= prev_d and k < d:
                    signals.append({'type': 'SELL', 'indicator': 'KD', 'reason': f'KD 高檔死亡交叉 (K={k:.1f})', 'strength': 2})
                    sell_signals += 2

        # 4. MACD 訊號
        macd, signal_line = latest.get('MACD'), latest.get('MACD_Signal')
        if pd.notna(macd) and pd.notna(signal_line) and prev is not None:
            prev_macd, prev_signal = prev.get('MACD'), prev.get('MACD_Signal')
            if pd.notna(prev_macd) and pd.notna(prev_signal):
                # MACD 黃金交叉
                if prev_macd <= prev_signal and macd > signal_line:
                    signals.append({'type': 'BUY', 'indicator': 'MACD', 'reason': 'MACD 黃金交叉', 'strength': 2})
                    buy_signals += 2
                # MACD 死亡交叉
                elif prev_macd >= prev_signal and macd < signal_line:
                    signals.append({'type': 'SELL', 'indicator': 'MACD', 'reason': 'MACD 死亡交叉', 'strength': 2})
                    sell_signals += 2

        # 5. 布林通道訊號
        bb_upper, bb_lower = latest.get('BB_Upper'), latest.get('BB_Lower')
        close = latest.get('close')
        if pd.notna(bb_upper) and pd.notna(bb_lower) and pd.notna(close):
            if close <= bb_lower:
                signals.append({'type': 'BUY', 'indicator': 'BB', 'reason': '股價觸及布林下軌', 'strength': 1})
                buy_signals += 1
            elif close >= bb_upper:
                signals.append({'type': 'SELL', 'indicator': 'BB', 'reason': '股價觸及布林上軌', 'strength': 1})
                sell_signals += 1

        # 生成綜合建議
        total_score = buy_signals - sell_signals
        if total_score >= 4:
            recommendation = '強烈買入訊號'
            action = 'STRONG_BUY'
        elif total_score >= 2:
            recommendation = '買入訊號'
            action = 'BUY'
        elif total_score <= -4:
            recommendation = '強烈賣出訊號'
            action = 'STRONG_SELL'
        elif total_score <= -2:
            recommendation = '賣出訊號'
            action = 'SELL'
        else:
            recommendation = '觀望，等待更明確訊號'
            action = 'HOLD'

        return {
            'signals': signals,
            'buy_score': buy_signals,
            'sell_score': sell_signals,
            'total_score': total_score,
            'recommendation': recommendation,
            'action': action
        }

    def find_buy_sell_points(self, df: pd.DataFrame) -> Dict[str, List]:
        """
        找出歷史買賣點

        Args:
            df: 包含技術指標的 DataFrame

        Returns:
            歷史買賣點列表
        """
        if df.empty or len(df) < 20:
            return {'buy_points': [], 'sell_points': []}

        buy_points = []
        sell_points = []

        for i in range(2, len(df)):
            curr = df.iloc[i]
            prev = df.iloc[i-1]

            buy_score = 0
            sell_score = 0

            # MA 交叉
            if pd.notna(curr.get('MA5')) and pd.notna(curr.get('MA20')):
                if pd.notna(prev.get('MA5')) and pd.notna(prev.get('MA20')):
                    if prev['MA5'] <= prev['MA20'] and curr['MA5'] > curr['MA20']:
                        buy_score += 2
                    elif prev['MA5'] >= prev['MA20'] and curr['MA5'] < curr['MA20']:
                        sell_score += 2

            # RSI
            rsi = curr.get('RSI')
            if pd.notna(rsi):
                if rsi < 30:
                    buy_score += 1
                elif rsi > 70:
                    sell_score += 1

            # KD 交叉
            k, d = curr.get('K'), curr.get('D')
            prev_k, prev_d = prev.get('K'), prev.get('D')
            if pd.notna(k) and pd.notna(d) and pd.notna(prev_k) and pd.notna(prev_d):
                if k < 30 and prev_k <= prev_d and k > d:
                    buy_score += 2
                elif k > 70 and prev_k >= prev_d and k < d:
                    sell_score += 2

            # 記錄買賣點
            if buy_score >= 2:
                buy_points.append({
                    'index': i,
                    'date': curr.get('date', ''),
                    'price': curr.get('close', 0),
                    'score': buy_score
                })
            elif sell_score >= 2:
                sell_points.append({
                    'index': i,
                    'date': curr.get('date', ''),
                    'price': curr.get('close', 0),
                    'score': sell_score
                })

        return {'buy_points': buy_points, 'sell_points': sell_points}

    def predict_future_trend(self, df: pd.DataFrame, days: int = 5) -> Dict[str, Any]:
        """
        預測未來走勢

        使用多種方法進行預測：
        1. 線性回歸趨勢
        2. 移動平均趨勢
        3. 技術指標綜合判斷
        4. 支撐壓力位分析

        Args:
            df: 包含技術指標的 DataFrame
            days: 預測天數

        Returns:
            預測結果
        """
        if df.empty or len(df) < 20:
            return {'error': '數據不足，無法進行預測'}

        import numpy as np

        closes = df['close'].values
        current_price = closes[-1]

        # 1. 使用近期數據進行線性回歸預測 (只用最近20天)
        recent_days = min(20, len(closes))
        recent_closes = closes[-recent_days:]
        x = np.arange(recent_days)
        coeffs = np.polyfit(x, recent_closes, 1)
        slope = coeffs[0]  # 每日變化斜率

        # 從當前價格開始預測，使用近期趨勢斜率
        # 但斜率影響會隨時間遞減（市場會趨於均值回歸）
        decay_factor = 0.8  # 趨勢衰減因子

        # 2. 移動平均趨勢
        ma5 = df['MA5'].iloc[-1] if 'MA5' in df.columns and pd.notna(df['MA5'].iloc[-1]) else current_price
        ma20 = df['MA20'].iloc[-1] if 'MA20' in df.columns and pd.notna(df['MA20'].iloc[-1]) else current_price

        ma_trend = 'UP' if ma5 > ma20 else 'DOWN'
        ma_diff_pct = ((ma5 - ma20) / ma20) * 100 if ma20 != 0 else 0

        # 3. 波動率計算 (用於預測區間)
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns) * np.sqrt(252)  # 年化波動率
        daily_volatility = volatility / np.sqrt(252)

        # 4. 技術指標趨勢分析
        trend_score = 0
        trend_factors = []

        # RSI 趨勢
        rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns and pd.notna(df['RSI'].iloc[-1]) else 50
        if rsi < 30:
            trend_score += 2
            trend_factors.append('RSI 超賣，可能反彈')
        elif rsi < 40:
            trend_score += 1
            trend_factors.append('RSI 偏低，有反彈空間')
        elif rsi > 70:
            trend_score -= 2
            trend_factors.append('RSI 超買，可能回調')
        elif rsi > 60:
            trend_score -= 1
            trend_factors.append('RSI 偏高，注意回調')

        # KD 趨勢
        k = df['K'].iloc[-1] if 'K' in df.columns and pd.notna(df['K'].iloc[-1]) else 50
        d = df['D'].iloc[-1] if 'D' in df.columns and pd.notna(df['D'].iloc[-1]) else 50
        if k < 20 and d < 20:
            trend_score += 2
            trend_factors.append('KD 低檔，反彈機率高')
        elif k > 80 and d > 80:
            trend_score -= 2
            trend_factors.append('KD 高檔，回調機率高')
        if k > d:
            trend_score += 1
            trend_factors.append('K > D，短期偏多')
        else:
            trend_score -= 1
            trend_factors.append('K < D，短期偏空')

        # MACD 趨勢
        macd = df['MACD'].iloc[-1] if 'MACD' in df.columns and pd.notna(df['MACD'].iloc[-1]) else 0
        macd_signal = df['MACD_Signal'].iloc[-1] if 'MACD_Signal' in df.columns and pd.notna(df['MACD_Signal'].iloc[-1]) else 0
        if macd > macd_signal:
            trend_score += 1
            trend_factors.append('MACD 多頭排列')
        else:
            trend_score -= 1
            trend_factors.append('MACD 空頭排列')

        # 均線趨勢
        if ma5 > ma20:
            trend_score += 1
            trend_factors.append('短期均線在長期均線上方')
        else:
            trend_score -= 1
            trend_factors.append('短期均線在長期均線下方')

        # 價格相對均線位置
        if current_price > ma5:
            trend_score += 1
            trend_factors.append('股價站上 MA5')
        else:
            trend_score -= 1
            trend_factors.append('股價跌破 MA5')

        # 5. 計算預測價格區間
        predictions = []
        for i in range(1, days + 1):
            # 從當前價格開始，使用斜率預測（帶衰減）
            # 斜率效果隨時間衰減，避免過度外推
            effective_slope = slope * (decay_factor ** (i - 1))
            base_price = current_price + effective_slope * i

            # 根據趨勢分數調整 (趨勢分數範圍約 -7 到 +7)
            # 每個趨勢分數貢獻約 0.2% 的每日變化
            trend_adjustment = (trend_score / 7) * current_price * 0.002 * i
            adjusted_price = base_price + trend_adjustment

            # 計算信賴區間 (95% 信賴區間)
            std_dev = current_price * daily_volatility * np.sqrt(i)
            upper_bound = adjusted_price + 1.96 * std_dev
            lower_bound = max(adjusted_price - 1.96 * std_dev, 0)  # 價格不能為負

            predictions.append({
                'day': i,
                'predicted_price': round(adjusted_price, 2),
                'upper_bound': round(upper_bound, 2),
                'lower_bound': round(lower_bound, 2),
                'change_pct': round(((adjusted_price - current_price) / current_price) * 100, 2)
            })

        # 6. 綜合判斷
        if trend_score >= 4:
            overall_trend = 'STRONG_UP'
            trend_description = '強勢上漲'
        elif trend_score >= 2:
            overall_trend = 'UP'
            trend_description = '偏多上漲'
        elif trend_score <= -4:
            overall_trend = 'STRONG_DOWN'
            trend_description = '強勢下跌'
        elif trend_score <= -2:
            overall_trend = 'DOWN'
            trend_description = '偏空下跌'
        else:
            overall_trend = 'NEUTRAL'
            trend_description = '盤整震盪'

        # 7. 計算目標價
        sr = self.calculate_support_resistance(df)
        support = sr.get('support', [])
        resistance = sr.get('resistance', [])

        if overall_trend in ['STRONG_UP', 'UP']:
            target_price = resistance[0] if resistance else current_price * 1.05
            stop_loss = support[0] if support else current_price * 0.95
        elif overall_trend in ['STRONG_DOWN', 'DOWN']:
            target_price = support[0] if support else current_price * 0.95
            stop_loss = resistance[0] if resistance else current_price * 1.05
        else:
            target_price = current_price
            stop_loss = support[0] if support else current_price * 0.97

        return {
            'current_price': current_price,
            'trend': overall_trend,
            'trend_description': trend_description,
            'trend_score': trend_score,
            'trend_factors': trend_factors,
            'predictions': predictions,
            'volatility': round(volatility * 100, 2),  # 百分比
            'daily_volatility': round(daily_volatility * 100, 2),
            'slope': round(slope, 4),
            'slope_direction': 'UP' if slope > 0 else 'DOWN',
            'ma_trend': ma_trend,
            'ma_diff_pct': round(ma_diff_pct, 2),
            'target_price': round(target_price, 2),
            'stop_loss': round(stop_loss, 2),
            'support_levels': support[:3],
            'resistance_levels': resistance[:3]
        }

