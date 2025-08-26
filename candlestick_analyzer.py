"""
🕯️ Pure Candlestick Analyzer (FIXED OHLC)
candlestick_analyzer.py

🔧 FIXED ISSUES:
✅ numpy.void object 'get' method error
✅ Proper OHLC data extraction from MT5
✅ Volume data handling
✅ Error handling for missing data

🚀 Features:
✅ OHLC Data Collection
✅ Candlestick Pattern Recognition
✅ Volume Analysis (with fallback)
✅ Body Ratio Calculation
✅ Price Direction Detection
✅ Basic Pattern Classification
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

class CandlestickAnalyzer:
    """
    🕯️ Pure Candlestick Analyzer (FIXED VERSION)
    
    วิเคราะห์แท่งเทียนปัจจุบันและก่อนหน้า
    เพื่อหา patterns และ signals ที่เชื่อถือได้
    """
    
    def __init__(self, mt5_connector, config: Dict):
        """
        🔧 เริ่มต้น Candlestick Analyzer
        
        Args:
            mt5_connector: MT5 connection object
            config: การตั้งค่าระบบ
        """
        self.mt5_connector = mt5_connector
        self.config = config
        
        # การตั้งค่า
        self.symbol = config.get("trading", {}).get("symbol", "XAUUSD.v")
        self.timeframe = mt5.TIMEFRAME_M5  # ใช้ 5 นาที
        
        # การตั้งค่า analysis
        self.min_candles_required = 20  # ต้องมีข้อมูลอย่างน้อย 20 แท่ง
        self.volume_lookback_periods = 10  # ดู volume ย้อนหลัง 10 periods
        
        # Pattern settings
        self.doji_threshold = 0.05  # body < 5% = doji
        self.strong_body_threshold = 0.6  # body > 60% = strong trend
        
        # Cache
        self.last_analysis_time = datetime.min
        self.cache_duration_seconds = 2  # cache 2 วินาที
        self.cached_analysis = None
        
        # Volume data
        self.volume_available = False
        self.volume_history = []
        
        print(f"🕯️ Candlestick Analyzer initialized for {self.symbol}")
        print(f"   Timeframe: M5")
        print(f"   Min candles: {self.min_candles_required}")
        print(f"   Volume lookback: {self.volume_lookback_periods}")
    
    # ==========================================
    # 📊 MAIN ANALYSIS METHODS
    # ==========================================
    
    def get_current_analysis(self) -> Optional[Dict]:
        """
        📊 ดึงการวิเคราะห์แท่งเทียนปัจจุบัน
        
        Returns:
            Dict: ผลการวิเคราะห์ หรือ None ถ้าเกิดปัญหา
        """
        try:
            # เช็ค cache
            if self._is_cache_valid():
                return self.cached_analysis.copy()
            
            # ตรวจสอบการเชื่อมต่อ
            if not self.mt5_connector.is_connected:
                print(f"❌ MT5 not connected - cannot analyze")
                return None
            
            # ดึงข้อมูล OHLC
            ohlc_data = self._get_ohlc_data()
            if not ohlc_data:
                print(f"❌ Cannot get OHLC data")
                return None
            
            current_candle = ohlc_data['current']
            previous_candle = ohlc_data['previous']
            
            # ดึงข้อมูล volume
            volume_data = self._get_volume_analysis()
            
            # วิเคราะห์แท่งเทียน
            candlestick_analysis = self._analyze_candlestick(current_candle, previous_candle)
            
            # รวมข้อมูลทั้งหมด
            complete_analysis = {
                # OHLC data
                'symbol': self.symbol,
                'timestamp': datetime.now(),
                'open': current_candle['open'],
                'high': current_candle['high'],
                'low': current_candle['low'],
                'close': current_candle['close'],
                'previous_close': previous_candle['close'],
                
                # Candlestick analysis
                'candle_color': candlestick_analysis['color'],
                'body_ratio': candlestick_analysis['body_ratio'],
                'price_direction': candlestick_analysis['price_direction'],
                'candle_range': candlestick_analysis['range'],
                'body_size': candlestick_analysis['body_size'],
                'upper_wick': candlestick_analysis['upper_wick'],
                'lower_wick': candlestick_analysis['lower_wick'],
                
                # Pattern recognition
                'pattern_name': candlestick_analysis['pattern_name'],
                'pattern_strength': candlestick_analysis['pattern_strength'],
                
                # Volume analysis
                'volume_available': volume_data['available'],
                'current_volume': volume_data['current'],
                'avg_volume': volume_data['average'],
                'volume_factor': volume_data['factor'],
                
                # Market context
                'market_context': self._get_market_context(current_candle),
                'analysis_strength': self._calculate_analysis_strength(candlestick_analysis, volume_data),
                
                # Metadata
                'timeframe': 'M5',
                'analysis_time': datetime.now()
            }
            
            # บันทึก cache
            self.cached_analysis = complete_analysis.copy()
            self.last_analysis_time = datetime.now()
            
            return complete_analysis
            
        except Exception as e:
            print(f"❌ Current analysis error: {e}")
            return None
    
    def _get_ohlc_data(self) -> Optional[Dict]:
        """
        📊 ดึงข้อมูล OHLC แท่งปัจจุบันและก่อนหน้า (FIXED)
        
        Returns:
            Dict: ข้อมูล current และ previous candle
        """
        try:
            # ดึงข้อมูล 3 แท่งล่าสุด (เพื่อความปลอดภัย)
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 3)
            
            if rates is None or len(rates) < 2:
                print(f"❌ Cannot get sufficient rate data for {self.symbol}")
                return None
            
            # 🔧 FIXED: แปลง numpy array เป็น dict อย่างถูกต้อง
            # แท่งปัจจุบัน (ล่าสุด)
            current_raw = rates[-1]
            current_candle = {
                'time': datetime.fromtimestamp(int(current_raw['time'])),
                'open': float(current_raw['open']),
                'high': float(current_raw['high']),
                'low': float(current_raw['low']),
                'close': float(current_raw['close']),
                'volume': int(current_raw['tick_volume']) if 'tick_volume' in current_raw.dtype.names else 0
            }
            
            # แท่งก่อนหน้า
            previous_raw = rates[-2]
            previous_candle = {
                'time': datetime.fromtimestamp(int(previous_raw['time'])),
                'open': float(previous_raw['open']),
                'high': float(previous_raw['high']),
                'low': float(previous_raw['low']),
                'close': float(previous_raw['close']),
                'volume': int(previous_raw['tick_volume']) if 'tick_volume' in previous_raw.dtype.names else 0
            }
            
            print(f"📊 OHLC retrieved: Current ${current_candle['close']:.2f}, Previous ${previous_candle['close']:.2f}")
            
            return {
                'current': current_candle,
                'previous': previous_candle,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ OHLC data error: {e}")
            return None
    
    def _analyze_candlestick(self, current: Dict, previous: Dict) -> Dict:
        """
        🕯️ วิเคราะห์แท่งเทียนปัจจุบัน
        
        Args:
            current: ข้อมูลแท่งปัจจุบัน
            previous: ข้อมูลแท่งก่อนหน้า
            
        Returns:
            Dict: ผลการวิเคราะห์แท่งเทียน
        """
        try:
            o, h, l, c = current['open'], current['high'], current['low'], current['close']
            prev_close = previous['close']
            
            # คำนวณขนาดต่างๆ
            candle_range = h - l
            body_size = abs(c - o)
            body_ratio = body_size / candle_range if candle_range > 0 else 0
            
            # กำหนดสีแท่งเทียน
            if c > o:
                candle_color = 'green'  # bullish
            elif c < o:
                candle_color = 'red'    # bearish
            else:
                candle_color = 'doji'   # เท่ากัน
            
            # ทิศทางราคา
            if c > prev_close:
                price_direction = 'higher_close'
            elif c < prev_close:
                price_direction = 'lower_close'
            else:
                price_direction = 'same_close'
            
            # คำนวณ wicks
            if candle_color == 'green':
                upper_wick = h - c
                lower_wick = o - l
            elif candle_color == 'red':
                upper_wick = h - o
                lower_wick = c - l
            else:  # doji
                upper_wick = h - max(o, c)
                lower_wick = min(o, c) - l
            
            # Pattern recognition
            pattern_info = self._recognize_basic_patterns({
                'color': candle_color,
                'body_ratio': body_ratio,
                'upper_wick': upper_wick,
                'lower_wick': lower_wick,
                'candle_range': candle_range
            })
            
            analysis_result = {
                'color': candle_color,
                'body_ratio': body_ratio,
                'price_direction': price_direction,
                'range': candle_range,
                'body_size': body_size,
                'upper_wick': upper_wick,
                'lower_wick': lower_wick,
                'pattern_name': pattern_info['name'],
                'pattern_strength': pattern_info['strength'],
                'analysis_quality': self._calculate_candle_quality(body_ratio, candle_range)
            }
            
            print(f"🕯️ Candle analysis: {candle_color} candle, body ratio {body_ratio:.3f}, {price_direction}")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Candlestick analysis error: {e}")
            return self._get_fallback_analysis()
    
    def _get_volume_analysis(self) -> Dict:
        """
        📊 วิเคราะห์ข้อมูล Volume (FIXED)
        
        Returns:
            Dict: ข้อมูล volume analysis
        """
        try:
            # ดึงข้อมูล volume ย้อนหลัง
            rates = mt5.copy_rates_from_pos(
                self.symbol, self.timeframe, 0, self.volume_lookback_periods + 1
            )
            
            if rates is None or len(rates) < self.volume_lookback_periods:
                print(f"⚠️ Volume data not available - using fallback")
                return {
                    'available': False,
                    'current': 0,
                    'average': 0,
                    'factor': 1.0,
                    'source': 'fallback'
                }
            
            # 🔧 FIXED: ดึง volumes โดยไม่ใช้ .get() method
            volumes = []
            for rate in rates:
                try:
                    if 'tick_volume' in rate.dtype.names:
                        volumes.append(int(rate['tick_volume']))
                    else:
                        volumes.append(0)
                except:
                    volumes.append(0)
            
            current_volume = volumes[-1] if volumes else 0  # แท่งล่าสุด
            historical_volumes = volumes[:-1] if len(volumes) > 1 else [current_volume]  # แท่งก่อนหน้า
            
            # คำนวณ average volume
            if historical_volumes and len(historical_volumes) > 0:
                avg_volume = sum(historical_volumes) / len(historical_volumes)
                volume_factor = current_volume / avg_volume if avg_volume > 0 else 1.0
            else:
                avg_volume = current_volume
                volume_factor = 1.0
            
            self.volume_available = True
            
            print(f"📊 Volume analysis: Current {current_volume}, Avg {avg_volume:.0f}, Factor {volume_factor:.2f}")
            
            return {
                'available': True,
                'current': current_volume,
                'average': avg_volume,
                'factor': volume_factor,
                'source': 'mt5'
            }
            
        except Exception as e:
            print(f"❌ Volume analysis error: {e}")
            return {
                'available': False,
                'current': 0,
                'average': 0,
                'factor': 1.0,
                'source': 'error'
            }
    
    # ==========================================
    # 🔍 PATTERN RECOGNITION
    # ==========================================
    
    def _recognize_basic_patterns(self, candle_data: Dict) -> Dict:
        """
        🔍 จำแนก Pattern พื้นฐาน
        
        Args:
            candle_data: ข้อมูลแท่งเทียน
            
        Returns:
            Dict: ข้อมูล pattern
        """
        try:
            color = candle_data.get('color', '')
            body_ratio = candle_data.get('body_ratio', 0)
            upper_wick = candle_data.get('upper_wick', 0)
            lower_wick = candle_data.get('lower_wick', 0)
            candle_range = candle_data.get('candle_range', 0)
            
            # คำนวณสัดส่วน wicks
            upper_wick_ratio = upper_wick / candle_range if candle_range > 0 else 0
            lower_wick_ratio = lower_wick / candle_range if candle_range > 0 else 0
            
            # จำแนก pattern
            if body_ratio < self.doji_threshold:
                # Doji patterns
                if upper_wick_ratio > 0.4:
                    pattern_name = 'dragonfly_doji' if lower_wick_ratio < 0.1 else 'long_legged_doji'
                elif lower_wick_ratio > 0.4:
                    pattern_name = 'gravestone_doji'
                else:
                    pattern_name = 'classic_doji'
                pattern_strength = 0.6
                
            elif body_ratio > self.strong_body_threshold:
                # Strong trend candles
                if color == 'green':
                    if lower_wick_ratio > 0.3:
                        pattern_name = 'hammer_bullish'
                        pattern_strength = 0.8
                    else:
                        pattern_name = 'strong_bullish'
                        pattern_strength = 0.7
                elif color == 'red':
                    if upper_wick_ratio > 0.3:
                        pattern_name = 'shooting_star'
                        pattern_strength = 0.8
                    else:
                        pattern_name = 'strong_bearish'
                        pattern_strength = 0.7
                else:
                    pattern_name = 'neutral'
                    pattern_strength = 0.5
                    
            else:
                # Standard candles
                if color == 'green':
                    pattern_name = 'green_candle'
                    pattern_strength = 0.5
                elif color == 'red':
                    pattern_name = 'red_candle'
                    pattern_strength = 0.5
                else:
                    pattern_name = 'neutral_candle'
                    pattern_strength = 0.3
            
            return {
                'name': pattern_name,
                'strength': pattern_strength,
                'body_ratio': body_ratio,
                'upper_wick_ratio': upper_wick_ratio,
                'lower_wick_ratio': lower_wick_ratio
            }
            
        except Exception as e:
            print(f"❌ Pattern recognition error: {e}")
            return {
                'name': 'unknown',
                'strength': 0.5,
                'body_ratio': 0,
                'upper_wick_ratio': 0,
                'lower_wick_ratio': 0
            }
    
    def _calculate_candle_quality(self, body_ratio: float, candle_range: float) -> float:
        """
        🎯 คำนวณคุณภาพของแท่งเทียน
        
        Args:
            body_ratio: สัดส่วน body
            candle_range: ขนาดแท่งเทียน
            
        Returns:
            float: คะแนนคุณภาพ 0-1
        """
        try:
            # คะแนนจาก body ratio
            if body_ratio >= 0.6:  # body แข็งแกร่ง
                ratio_score = 1.0
            elif body_ratio >= 0.3:  # body ปานกลาง
                ratio_score = 0.7
            elif body_ratio >= 0.1:  # body อ่อน
                ratio_score = 0.4
            else:  # doji หรือ body เล็กมาก
                ratio_score = 0.2
            
            # คะแนนจาก candle range (ความผันผวน)
            if candle_range >= 5.0:  # แท่งใหญ่
                range_score = 1.0
            elif candle_range >= 2.0:  # แท่งปานกลาง
                range_score = 0.8
            elif candle_range >= 1.0:  # แท่งเล็ก
                range_score = 0.6
            else:  # แท่งเล็กมาก
                range_score = 0.3
            
            # รวมคะแนน (เน้น body ratio)
            final_score = (ratio_score * 0.7) + (range_score * 0.3)
            
            return round(final_score, 3)
            
        except Exception as e:
            print(f"❌ Candle quality calculation error: {e}")
            return 0.5
    
    def _calculate_analysis_strength(self, candlestick_data: Dict, volume_data: Dict) -> float:
        """
        💪 คำนวณความแข็งแกร่งของการวิเคราะห์
        
        Args:
            candlestick_data: ผลการวิเคราะห์แท่งเทียน
            volume_data: ผลการวิเคราะห์ volume
            
        Returns:
            float: คะแนนความแข็งแกร่ง 0-1
        """
        try:
            # คะแนนจาก pattern
            pattern_strength = candlestick_data.get('strength', 0.5)
            
            # คะแนนจาก volume
            if volume_data['available']:
                volume_factor = volume_data['factor']
                if volume_factor >= 1.5:  # volume สูง
                    volume_score = 1.0
                elif volume_factor >= 1.2:  # volume ปานกลาง
                    volume_score = 0.8
                else:  # volume ปกติหรือต่ำ
                    volume_score = 0.6
            else:
                volume_score = 0.7  # ไม่มี volume = คะแนนกลางๆ
            
            # คะแนนจาก body ratio
            body_ratio = candlestick_data.get('body_ratio', 0)
            if body_ratio >= 0.4:
                body_score = 1.0
            elif body_ratio >= 0.2:
                body_score = 0.8
            else:
                body_score = 0.5
            
            # รวมคะแนน
            final_strength = (
                pattern_strength * 0.4 +
                volume_score * 0.3 +
                body_score * 0.3
            )
            
            return round(final_strength, 3)
            
        except Exception as e:
            print(f"❌ Analysis strength calculation error: {e}")
            return 0.5
    
    def _get_market_context(self, current_candle: Dict) -> str:
        """
        🌍 ดึงข้อมูล Market Context
        
        Args:
            current_candle: ข้อมูลแท่งปัจจุบัน
            
        Returns:
            str: ประเภท market context
        """
        try:
            # ตรวจสอบ trading session
            current_time = datetime.now()
            hour = current_time.hour
            
            if 1 <= hour < 9:    # Asian session
                session = 'asian'
            elif 9 <= hour < 17:  # London session
                session = 'london'
            elif 17 <= hour < 24: # New York session
                session = 'newyork'
            else:                 # Overlap
                session = 'overlap'
            
            # ดูความผันผวน
            candle_range = current_candle['high'] - current_candle['low']
            if candle_range >= 5.0:
                volatility = 'high'
            elif candle_range >= 2.0:
                volatility = 'medium'
            else:
                volatility = 'low'
            
            return f"{session}_{volatility}"
            
        except Exception as e:
            print(f"❌ Market context error: {e}")
            return "unknown_medium"
    
    # ==========================================
    # 🔧 UTILITY & HELPER METHODS
    # ==========================================
    
    def _is_cache_valid(self) -> bool:
        """🔧 ตรวจสอบ Cache"""
        try:
            if self.cached_analysis is None:
                return False
            
            time_diff = (datetime.now() - self.last_analysis_time).total_seconds()
            return time_diff < self.cache_duration_seconds
            
        except Exception as e:
            return False
    
    def _get_fallback_analysis(self) -> Dict:
        """⚠️ ข้อมูล fallback เมื่อ analysis ล้มเหลว"""
        return {
            'color': 'neutral',
            'body_ratio': 0.1,
            'price_direction': 'same_close',
            'range': 1.0,
            'body_size': 0.1,
            'upper_wick': 0.45,
            'lower_wick': 0.45,
            'pattern_name': 'error',
            'pattern_strength': 0.0,
            'analysis_quality': 0.0
        }
    
    def refresh_cache(self):
        """🔄 บังคับ refresh cache"""
        try:
            self.cached_analysis = None
            self.last_analysis_time = datetime.min
            print(f"🔄 Analysis cache refreshed")
        except Exception as e:
            print(f"❌ Cache refresh error: {e}")
    
    def is_ready(self) -> bool:
        """✅ ตรวจสอบความพร้อม"""
        return (
            self.mt5_connector is not None and
            self.mt5_connector.is_connected and
            self.symbol is not None
        )
    
    def get_analyzer_info(self) -> Dict:
        """ℹ️ ข้อมูล Candlestick Analyzer"""
        return {
            'name': 'Pure Candlestick Analyzer',
            'version': '1.0.0',
            'symbol': self.symbol,
            'timeframe': 'M5',
            'volume_available': self.volume_available,
            'min_candles_required': self.min_candles_required,
            'volume_lookback_periods': self.volume_lookback_periods,
            'doji_threshold': self.doji_threshold,
            'strong_body_threshold': self.strong_body_threshold,
            'cache_duration_seconds': self.cache_duration_seconds
        }

# ==========================================
# 🧪 TESTING & VALIDATION
# ==========================================

def test_candlestick_analyzer(mt5_connector, config):
    """🧪 ทดสอบ Candlestick Analyzer"""
    print("🧪 Testing Candlestick Analyzer...")
    print("=" * 50)
    
    analyzer = CandlestickAnalyzer(mt5_connector, config)
    
    if not analyzer.is_ready():
        print("❌ Analyzer not ready")
        return
    
    # ทดสอบการวิเคราะห์
    analysis = analyzer.get_current_analysis()
    
    if analysis:
        print("✅ Analysis successful!")
        print(f"   Symbol: {analysis.get('symbol')}")
        print(f"   Close: ${analysis.get('close', 0):.2f}")
        print(f"   Color: {analysis.get('candle_color')}")
        print(f"   Body ratio: {analysis.get('body_ratio', 0):.3f}")
        print(f"   Price direction: {analysis.get('price_direction')}")
        print(f"   Pattern: {analysis.get('pattern_name')}")
        print(f"   Volume available: {analysis.get('volume_available')}")
        print(f"   Analysis strength: {analysis.get('analysis_strength', 0):.2f}")
    else:
        print("❌ Analysis failed")
    
    print("=" * 50)
    print("✅ Candlestick Analyzer test completed")