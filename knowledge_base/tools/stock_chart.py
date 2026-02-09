"""股票圖表生成模組"""

import os
import subprocess
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用非互動式後端
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import warnings

warnings.filterwarnings('ignore')


def _open_image(filepath: str):
    """使用系統預設程式開啟圖片"""
    try:
        # Linux
        subprocess.Popen(['xdg-open', filepath],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
    except:
        try:
            # macOS
            subprocess.Popen(['open', filepath])
        except:
            try:
                # Windows
                os.startfile(filepath)
            except:
                pass


def _get_project_root():
    """獲取專案根目錄"""
    # 從當前檔案位置往上找專案根目錄
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # knowledge_base/tools -> knowledge_base -> project_root
    project_root = os.path.dirname(os.path.dirname(current_dir))
    return project_root


def _get_chinese_font():
    """獲取中文字體"""
    project_root = _get_project_root()

    # 優先使用專案內的字體
    project_font_paths = [
        os.path.join(project_root, 'fonts', 'NotoSansCJK-Regular.ttc'),
        os.path.join(project_root, 'fonts', 'NotoSansCJK-Bold.ttc'),
    ]

    # 系統字體作為備用
    system_font_paths = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
        '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
    ]

    # 先嘗試專案內字體
    for path in project_font_paths + system_font_paths:
        if os.path.exists(path):
            return fm.FontProperties(fname=path)

    # 如果找不到字體檔案，嘗試用字體名稱
    preferred_fonts = [
        'Noto Sans CJK JP',
        'Noto Sans CJK TC',
        'Noto Sans CJK SC',
        'Droid Sans Fallback',
        'WenQuanYi Micro Hei',
    ]

    available_fonts = set(f.name for f in fm.fontManager.ttflist)
    for font in preferred_fonts:
        if font in available_fonts:
            return fm.FontProperties(family=font)

    return None


# 全域中文字體
CHINESE_FONT = _get_chinese_font()

# 設定 matplotlib 預設字體
plt.rcParams['axes.unicode_minus'] = False
if CHINESE_FONT:
    plt.rcParams['font.family'] = CHINESE_FONT.get_family()
    font_name = CHINESE_FONT.get_name()
    if font_name:
        plt.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans']


class StockChartGenerator:
    """股票圖表生成器"""

    def __init__(self, output_dir: str = "charts", show_chart: bool = True):
        """
        初始化圖表生成器

        Args:
            output_dir: 圖表輸出目錄
            show_chart: 是否直接顯示圖表 (使用 plt.show())
        """
        self.output_dir = output_dir
        self.show_chart = show_chart
        os.makedirs(output_dir, exist_ok=True)
    
    def _parse_date(self, date_str: str) -> datetime:
        """解析民國年日期格式"""
        try:
            # 格式: 115/02/06
            parts = date_str.split('/')
            year = int(parts[0]) + 1911  # 民國年轉西元年
            month = int(parts[1])
            day = int(parts[2])
            return datetime(year, month, day)
        except:
            return datetime.now()
    
    def generate_price_chart(
        self,
        df: pd.DataFrame,
        stock_id: str,
        stock_name: str = "",
        buy_points: List[Dict] = None,
        sell_points: List[Dict] = None,
        support_levels: List[float] = None,
        resistance_levels: List[float] = None
    ) -> str:
        """
        生成股價走勢圖
        
        Args:
            df: 包含 OHLCV 和技術指標的 DataFrame
            stock_id: 股票代碼
            stock_name: 股票名稱
            buy_points: 買入點列表
            sell_points: 賣出點列表
            support_levels: 支撐位列表
            resistance_levels: 壓力位列表
            
        Returns:
            圖表檔案路徑
        """
        if df.empty:
            return ""
        
        # 轉換日期
        df = df.copy()
        df['datetime'] = df['date'].apply(self._parse_date)
        
        # 創建圖表
        fig, axes = plt.subplots(4, 1, figsize=(14, 12),
                                  gridspec_kw={'height_ratios': [3, 1, 1, 1]})

        # 設定標題（使用中文字體）
        title = f'{stock_id} {stock_name} 技術分析圖'
        if CHINESE_FONT:
            fig.suptitle(title, fontsize=16, fontweight='bold', fontproperties=CHINESE_FONT)
        else:
            fig.suptitle(title, fontsize=16, fontweight='bold')
        
        # 1. 價格圖 + 均線 + 布林通道
        ax1 = axes[0]
        self._plot_price_with_ma(ax1, df, buy_points, sell_points, 
                                  support_levels, resistance_levels)
        
        # 2. 成交量
        ax2 = axes[1]
        self._plot_volume(ax2, df)
        
        # 3. RSI
        ax3 = axes[2]
        self._plot_rsi(ax3, df)
        
        # 4. MACD
        ax4 = axes[3]
        self._plot_macd(ax4, df)
        
        # 調整佈局
        plt.tight_layout()

        # 儲存圖表
        filename = f"{stock_id}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        # 直接顯示圖表 (使用系統圖片檢視器)
        if self.show_chart:
            _open_image(filepath)

        return filepath
    
    def _plot_price_with_ma(
        self, ax, df: pd.DataFrame,
        buy_points: List[Dict] = None,
        sell_points: List[Dict] = None,
        support_levels: List[float] = None,
        resistance_levels: List[float] = None
    ):
        """繪製價格圖和均線"""
        dates = df['datetime']
        fp = CHINESE_FONT  # 中文字體

        # 繪製收盤價
        ax.plot(dates, df['close'], label='Close', color='#1f77b4', linewidth=1.5)

        # 繪製均線
        if 'MA5' in df.columns and df['MA5'].notna().any():
            ax.plot(dates, df['MA5'], label='MA5', color='#ff7f0e', linewidth=1, alpha=0.8)
        if 'MA10' in df.columns and df['MA10'].notna().any():
            ax.plot(dates, df['MA10'], label='MA10', color='#2ca02c', linewidth=1, alpha=0.8)
        if 'MA20' in df.columns and df['MA20'].notna().any():
            ax.plot(dates, df['MA20'], label='MA20', color='#d62728', linewidth=1, alpha=0.8)

        # 繪製布林通道
        if 'BB_Upper' in df.columns and df['BB_Upper'].notna().any():
            ax.fill_between(dates, df['BB_Lower'], df['BB_Upper'],
                           alpha=0.1, color='gray', label='BB')
            ax.plot(dates, df['BB_Upper'], color='gray', linewidth=0.5, linestyle='--')
            ax.plot(dates, df['BB_Lower'], color='gray', linewidth=0.5, linestyle='--')

        # 繪製買賣點
        buy_labeled = False
        if buy_points:
            for point in buy_points:
                idx = point.get('index', 0)
                if idx < len(df):
                    label = 'BUY' if not buy_labeled else None
                    ax.scatter(df['datetime'].iloc[idx], df['close'].iloc[idx],
                              marker='^', color='red', s=100, zorder=5, label=label)
                    buy_labeled = True

        sell_labeled = False
        if sell_points:
            for point in sell_points:
                idx = point.get('index', 0)
                if idx < len(df):
                    label = 'SELL' if not sell_labeled else None
                    ax.scatter(df['datetime'].iloc[idx], df['close'].iloc[idx],
                              marker='v', color='green', s=100, zorder=5, label=label)
                    sell_labeled = True

        # 繪製支撐壓力位
        if support_levels:
            for level in support_levels[:2]:
                ax.axhline(y=level, color='green', linestyle='--', alpha=0.5, linewidth=1)
                text_props = {'va': 'center', 'fontsize': 8, 'color': 'green'}
                if fp:
                    text_props['fontproperties'] = fp
                ax.text(dates.iloc[-1], level, f' S {level:.2f}', **text_props)

        if resistance_levels:
            for level in resistance_levels[:2]:
                ax.axhline(y=level, color='red', linestyle='--', alpha=0.5, linewidth=1)
                text_props = {'va': 'center', 'fontsize': 8, 'color': 'red'}
                if fp:
                    text_props['fontproperties'] = fp
                ax.text(dates.iloc[-1], level, f' R {level:.2f}', **text_props)

        # Y軸標籤
        if fp:
            ax.set_ylabel('Price', fontsize=10, fontproperties=fp)
        else:
            ax.set_ylabel('Price', fontsize=10)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    def _plot_volume(self, ax, df: pd.DataFrame):
        """繪製成交量圖"""
        dates = df['datetime']
        volumes = df['volume']
        fp = CHINESE_FONT

        # 根據漲跌設定顏色
        colors = []
        for i in range(len(df)):
            if i == 0:
                colors.append('#1f77b4')
            elif df['close'].iloc[i] >= df['close'].iloc[i-1]:
                colors.append('#d62728')  # 紅色 (上漲)
            else:
                colors.append('#2ca02c')  # 綠色 (下跌)

        ax.bar(dates, volumes, color=colors, alpha=0.7, width=0.8)
        if fp:
            ax.set_ylabel('Volume', fontsize=10, fontproperties=fp)
        else:
            ax.set_ylabel('Volume', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

        # 格式化 Y 軸
        ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))

    def _plot_rsi(self, ax, df: pd.DataFrame):
        """繪製 RSI 指標"""
        fp = CHINESE_FONT
        if 'RSI' not in df.columns or df['RSI'].isna().all():
            text_props = {'ha': 'center', 'va': 'center', 'transform': ax.transAxes}
            if fp:
                text_props['fontproperties'] = fp
            ax.text(0.5, 0.5, 'RSI Data Insufficient', **text_props)
            return

        dates = df['datetime']
        rsi = df['RSI']

        ax.plot(dates, rsi, label='RSI(14)', color='#9467bd', linewidth=1.5)

        # 超買超賣線
        ax.axhline(y=70, color='red', linestyle='--', alpha=0.5, linewidth=1)
        ax.axhline(y=30, color='green', linestyle='--', alpha=0.5, linewidth=1)
        ax.axhline(y=50, color='gray', linestyle='-', alpha=0.3, linewidth=1)

        # 填充超買超賣區域
        ax.fill_between(dates, 70, 100, alpha=0.1, color='red')
        ax.fill_between(dates, 0, 30, alpha=0.1, color='green')

        if fp:
            ax.set_ylabel('RSI', fontsize=10, fontproperties=fp)
        else:
            ax.set_ylabel('RSI', fontsize=10)
        ax.set_ylim(0, 100)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    def _plot_macd(self, ax, df: pd.DataFrame):
        """繪製 MACD 指標"""
        fp = CHINESE_FONT
        if 'MACD' not in df.columns or df['MACD'].isna().all():
            text_props = {'ha': 'center', 'va': 'center', 'transform': ax.transAxes}
            if fp:
                text_props['fontproperties'] = fp
            ax.text(0.5, 0.5, 'MACD Data Insufficient', **text_props)
            return

        dates = df['datetime']
        macd = df['MACD']
        signal = df['MACD_Signal']

        # MACD 柱狀圖
        histogram = macd - signal
        colors = ['#d62728' if h >= 0 else '#2ca02c' for h in histogram]
        ax.bar(dates, histogram, color=colors, alpha=0.5, width=0.8, label='Hist')

        # MACD 線和信號線
        ax.plot(dates, macd, label='MACD', color='#1f77b4', linewidth=1.2)
        ax.plot(dates, signal, label='Signal', color='#ff7f0e', linewidth=1.2)

        # 零軸
        ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5, linewidth=1)

        if fp:
            ax.set_ylabel('MACD', fontsize=10, fontproperties=fp)
            ax.set_xlabel('Date', fontsize=10, fontproperties=fp)
        else:
            ax.set_ylabel('MACD', fontsize=10)
            ax.set_xlabel('Date', fontsize=10)
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    def _plot_prediction(
        self, ax, last_date: datetime, current_price: float,
        predictions: List[Dict], trend: str
    ):
        """繪製預測走勢"""
        fp = CHINESE_FONT

        if not predictions:
            return

        # 建立預測日期（跳過週末）
        pred_dates = [last_date]
        pred_prices = [current_price]
        upper_bounds = [current_price]
        lower_bounds = [current_price]

        current_date = last_date
        for pred in predictions:
            # 計算下一個交易日（跳過週末）
            current_date = current_date + timedelta(days=1)
            while current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                current_date = current_date + timedelta(days=1)

            pred_dates.append(current_date)
            pred_prices.append(pred['predicted_price'])
            upper_bounds.append(pred['upper_bound'])
            lower_bounds.append(pred['lower_bound'])

        # 繪製信賴區間（填充區域）
        ax.fill_between(pred_dates, lower_bounds, upper_bounds,
                       alpha=0.2, color='purple', label='95% CI')

        # 繪製預測價格線
        trend_color = '#2ca02c' if 'UP' in trend else '#d62728' if 'DOWN' in trend else '#1f77b4'
        ax.plot(pred_dates, pred_prices, label='Prediction',
               color=trend_color, linewidth=2, linestyle='--', marker='o', markersize=4)

        # 標記起始點
        ax.scatter([last_date], [current_price], color='blue', s=100, zorder=5, marker='*')

        # 在最後一個預測點標記價格
        last_pred = predictions[-1]
        text_props = {'fontsize': 9, 'color': trend_color}
        if fp:
            text_props['fontproperties'] = fp
        ax.annotate(
            f'{last_pred["predicted_price"]:.2f}\n({last_pred["change_pct"]:+.2f}%)',
            xy=(pred_dates[-1], pred_prices[-1]),
            xytext=(10, 0),
            textcoords='offset points',
            ha='left',
            va='center',
            **text_props
        )

    def generate_prediction_chart(
        self,
        df: pd.DataFrame,
        predictions: Dict[str, Any],
        stock_id: str,
        stock_name: str = ""
    ) -> str:
        """
        生成包含預測的股價走勢圖

        Args:
            df: 包含 OHLCV 和技術指標的 DataFrame
            predictions: 預測結果（來自 predict_future_trend）
            stock_id: 股票代碼
            stock_name: 股票名稱

        Returns:
            圖表檔案路徑
        """
        if df.empty or 'predictions' not in predictions:
            return ""

        # 轉換日期
        df = df.copy()
        df['datetime'] = df['date'].apply(self._parse_date)

        # 只使用最近 30 天的數據
        df_recent = df.tail(30).copy()

        # 創建圖表
        fig, axes = plt.subplots(2, 1, figsize=(14, 10),
                                  gridspec_kw={'height_ratios': [3, 1]})

        # 設定標題
        trend_desc = predictions.get('trend_description', '')
        title = f'{stock_id} {stock_name} - 走勢預測 ({trend_desc})'
        if CHINESE_FONT:
            fig.suptitle(title, fontsize=16, fontweight='bold', fontproperties=CHINESE_FONT)
        else:
            fig.suptitle(title, fontsize=16, fontweight='bold')

        # 1. 歷史價格 + 預測
        ax1 = axes[0]
        dates = df_recent['datetime']

        # 繪製歷史收盤價
        ax1.plot(dates, df_recent['close'], label='Close', color='#1f77b4', linewidth=1.5)

        # 繪製均線
        if 'MA5' in df_recent.columns:
            ax1.plot(dates, df_recent['MA5'], label='MA5', color='#ff7f0e', linewidth=1, alpha=0.8)
        if 'MA20' in df_recent.columns:
            ax1.plot(dates, df_recent['MA20'], label='MA20', color='#d62728', linewidth=1, alpha=0.8)

        # 繪製預測
        last_date = df_recent['datetime'].iloc[-1]
        current_price = predictions['current_price']
        self._plot_prediction(ax1, last_date, current_price,
                             predictions['predictions'], predictions['trend'])

        # 繪製目標價和停損價
        target = predictions.get('target_price')
        stop_loss = predictions.get('stop_loss')
        if target:
            ax1.axhline(y=target, color='green', linestyle=':', alpha=0.7, linewidth=1.5)
            text_props = {'va': 'center', 'fontsize': 9, 'color': 'green'}
            if CHINESE_FONT:
                text_props['fontproperties'] = CHINESE_FONT
            ax1.text(dates.iloc[-1], target, f' Target: {target:.2f}', **text_props)
        if stop_loss:
            ax1.axhline(y=stop_loss, color='red', linestyle=':', alpha=0.7, linewidth=1.5)
            text_props = {'va': 'center', 'fontsize': 9, 'color': 'red'}
            if CHINESE_FONT:
                text_props['fontproperties'] = CHINESE_FONT
            ax1.text(dates.iloc[-1], stop_loss, f' StopLoss: {stop_loss:.2f}', **text_props)

        if CHINESE_FONT:
            ax1.set_ylabel('Price', fontsize=10, fontproperties=CHINESE_FONT)
        else:
            ax1.set_ylabel('Price', fontsize=10)
        ax1.legend(loc='upper left', fontsize=8)
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

        # 2. 預測摘要資訊
        ax2 = axes[1]
        ax2.axis('off')

        # 建立摘要文字
        info_lines = [
            f"Current: {predictions['current_price']:.2f}  |  ",
            f"Trend: {predictions['trend_description']} (Score: {predictions['trend_score']:+d})  |  ",
            f"Volatility: {predictions['volatility']:.1f}%  |  ",
            f"Target: {predictions.get('target_price', 'N/A')}  |  ",
            f"StopLoss: {predictions.get('stop_loss', 'N/A')}"
        ]

        # 趨勢因素
        factors = predictions.get('trend_factors', [])
        factors_text = '  •  '.join(factors[:4]) if factors else 'N/A'

        summary = ''.join(info_lines) + '\n\nFactors: ' + factors_text

        text_props = {'fontsize': 11, 'va': 'top', 'ha': 'left',
                     'family': 'monospace', 'wrap': True}
        if CHINESE_FONT:
            text_props['fontproperties'] = CHINESE_FONT
        ax2.text(0.02, 0.9, summary, transform=ax2.transAxes, **text_props)

        plt.tight_layout()

        # 儲存圖表
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{stock_id}_prediction_{timestamp}.png'
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()

        # 直接顯示圖表 (使用系統圖片檢視器)
        if self.show_chart:
            _open_image(filepath)

        return filepath

    def generate_summary_text(
        self,
        stock_id: str,
        stock_name: str,
        trading_signals: Dict[str, Any],
        support_resistance: Dict[str, Any]
    ) -> str:
        """
        生成分析摘要文字

        Args:
            stock_id: 股票代碼
            stock_name: 股票名稱
            trading_signals: 交易訊號
            support_resistance: 支撐壓力位

        Returns:
            分析摘要文字
        """
        lines = []
        lines.append(f"📊 {stock_id} {stock_name} 技術分析報告")
        lines.append("=" * 40)

        # 交易建議
        action = trading_signals.get('action', 'HOLD')
        recommendation = trading_signals.get('recommendation', '觀望')
        action_emoji = {
            'STRONG_BUY': '🔥 強烈買入',
            'BUY': '📈 買入',
            'HOLD': '⏸️ 觀望',
            'SELL': '📉 賣出',
            'STRONG_SELL': '⚠️ 強烈賣出'
        }
        lines.append(f"\n💡 交易建議: {action_emoji.get(action, recommendation)}")
        lines.append(f"   買入分數: {trading_signals.get('buy_score', 0)}")
        lines.append(f"   賣出分數: {trading_signals.get('sell_score', 0)}")

        # 訊號列表
        signals = trading_signals.get('signals', [])
        if signals:
            lines.append("\n📋 技術指標訊號:")
            for sig in signals:
                sig_type = '🟢' if sig['type'] == 'BUY' else '🔴'
                lines.append(f"   {sig_type} [{sig['indicator']}] {sig['reason']}")

        # 支撐壓力位
        support = support_resistance.get('support', [])
        resistance = support_resistance.get('resistance', [])
        current = support_resistance.get('current_price', 0)

        lines.append(f"\n📍 當前價格: {current:.2f}")

        if resistance:
            lines.append("⬆️ 壓力位:")
            for r in resistance[:3]:
                pct = ((r - current) / current) * 100
                lines.append(f"   {r:.2f} (+{pct:.1f}%)")

        if support:
            lines.append("⬇️ 支撐位:")
            for s in support[:3]:
                pct = ((current - s) / current) * 100
                lines.append(f"   {s:.2f} (-{pct:.1f}%)")

        return "\n".join(lines)

