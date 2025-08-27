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
        🔧 เริ่มต้น Candlestick Analyzer - เพิ่ม tracking
        """
        self.mt5_connector = mt5_connector
        self.config = config
        
        # การตั้งค่า
        self.symbol = config.get("trading", {}).get("symbol", "XAUUSD.v")
        self.timeframe = mt5.TIMEFRAME_M5
        
        # การตั้งค่า analysis
        self.min_candles_required = 20
        self.volume_lookback_periods = 10
        
        # Pattern settings
        self.doji_threshold = 0.05
        self.strong_body_threshold = 0.6
        
        # Cache
        self.last_analysis_time = datetime.min
        self.last_analyzed_candle_time = datetime.min  # 🔧 NEW: ติดตามแท่งล่าสุดที่วิเคราะห์
        self.cache_duration_seconds = 60
        self.cached_analysis = None
        
        # Volume data
        self.volume_available = False
        self.volume_history = []
        
        print(f"🕯️ Real-time Candlestick Analyzer initialized for {self.symbol}")
        print(f"   Will detect new candles immediately upon close")
    
    # ==========================================
    # 📊 MAIN ANALYSIS METHODS
    # ==========================================
    
    def get_current_analysis(self) -> Optional[Dict]:
        """
        📊 ตรวจจับและวิเคราะห์แท่งที่เพิ่งปิดใหม่ - FORCE DETECTION MODE
        
        Returns:
            Dict: ผลการวิเคราะห์ หรือ None ถ้ายังไม่มีแท่งใหม่
        """
        try:
            # ตรวจสอบการเชื่อมต่อ
            if not self.mt5_connector.is_connected:
                print(f"❌ MT5 not connected - cannot analyze")
                return None
            
            print(f"🔍 === CANDLESTICK ANALYSIS CYCLE ===")
            
            # 🔧 IMPROVED: ตรวจจับแท่งใหม่แบบ aggressive
            new_closed_candle = self._detect_new_closed_candle()
            
            if not new_closed_candle:
                print(f"⏳ No new candle detected - using cache if available")
                # ส่งคืน cache หรือ None
                if self._is_cache_valid() and self.cached_analysis:
                    cached = self.cached_analysis.copy()
                    cached['is_cached'] = True
                    cached['has_new_candle'] = False
                    print(f"📋 Returning cached analysis")
                    return cached
                else:
                    print(f"❌ No cached data available")
                    return None
            
            # มีแท่งใหม่! - วิเคราะห์ทันที
            print(f"🕯️ === NEW CANDLE ANALYSIS START ===")
            
            current_candle = new_closed_candle['current']
            previous_candle = new_closed_candle['previous']
            
            # ดึงข้อมูล volume
            volume_data = self._get_volume_analysis()
            
            # วิเคราะห์แท่งเทียน
            candlestick_analysis = self._analyze_candlestick(current_candle, previous_candle)
            
            # รวมข้อมูลทั้งหมด
            complete_analysis = {
                # OHLC data
                'symbol': self.symbol,
                'timestamp': datetime.now(),
                'candle_time': current_candle['time'],
                'open': current_candle['open'],
                'high': current_candle['high'],
                'low': current_candle['low'],
                'close': current_candle['close'],
                'previous_close': previous_candle['close'],
                
                # 🔧 NEW: ข้อมูลการตรวจจับ
                'has_new_candle': True,
                'is_fresh_analysis': True,
                'candle_close_time': current_candle['time'],
                'detection_method': 'real_time',
                
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
                'analysis_time': datetime.now(),
                'is_cached': False
            }
            
            # 🔧 IMPROVED: อัพเดท tracking
            self.cached_analysis = complete_analysis.copy()
            self.last_analysis_time = datetime.now()
            self.last_analyzed_candle_time = current_candle['time']
            self.cache_duration_seconds = 240  # 4 minutes cache
            
            print(f"✅ === FRESH ANALYSIS COMPLETED ===")
            print(f"   Signal ready for: {candlestick_analysis['color']} candle")
            print(f"   Price direction: {candlestick_analysis['price_direction']}")
            print(f"   Body ratio: {candlestick_analysis['body_ratio']:.3f}")
            print(f"   Pattern: {candlestick_analysis['pattern_name']}")
            print(f"   Cached until: {(datetime.now() + timedelta(seconds=240)).strftime('%H:%M:%S')}")
            
            return complete_analysis
            
        except Exception as e:
            print(f"❌ Current analysis error: {e}")
            return None
            
    def _detect_new_closed_candle(self) -> Optional[Dict]:
        """
        🔍 ตรวจจับแท่งใหม่ที่เพิ่งปิด - IMPROVED DETECTION
        
        Returns:
            Dict: ข้อมูลแท่งใหม่ หรือ None ถ้าไม่มีแท่งใหม่
        """
        try:
            # ดึงข้อมูล 3 แท่งล่าสุดที่ปิดแล้ว (เพิ่มขึ้นเพื่อความแม่นยำ)
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 1, 3)
            
            if rates is None or len(rates) < 2:
                print(f"❌ Cannot get rate data for new candle detection")
                return None
            
            # แปลงข้อมูล
            current_raw = rates[0]  # แท่งที่ปิดล่าสุด
            current_time = datetime.fromtimestamp(int(current_raw['time']))
            
            print(f"🔍 Checking candle at {current_time.strftime('%H:%M:%S')}")
            
            # 🔧 IMPROVED: เช็คการเปลี่ยนแปลงแท่งแบบละเอียด
            is_new_candle = False
            
            if hasattr(self, 'last_analyzed_candle_time'):
                time_diff = (current_time - self.last_analyzed_candle_time).total_seconds()
                print(f"   Time diff from last analysis: {time_diff:.0f} seconds")
                
                # แท่งใหม่ต้องมาหลังจากแท่งเดิมอย่างน้อย 4 นาที
                if time_diff >= 240:  # 4 minutes
                    is_new_candle = True
                    print(f"   ✅ NEW CANDLE: Time difference sufficient")
                else:
                    print(f"   ⏳ Same candle: Time difference too small ({time_diff:.0f}s)")
                    return None
            else:
                # ยังไม่เคยวิเคราะห์ - ถือว่าแท่งใหม่
                is_new_candle = True
                print(f"   ✅ FIRST ANALYSIS: Treating as new candle")
            
            # ตรวจสอบอายุแท่ง (ไม่เก่าเกิน 15 นาที)
            candle_age_minutes = (datetime.now() - current_time).total_seconds() / 60
            if candle_age_minutes > 15:
                print(f"   ❌ Candle too old: {candle_age_minutes:.1f} minutes")
                return None
            
            # เตรียมข้อมูลแท่ง
            current_candle = {
                'time': current_time,
                'open': float(current_raw['open']),
                'high': float(current_raw['high']),
                'low': float(current_raw['low']),
                'close': float(current_raw['close']),
                'volume': int(current_raw['tick_volume']) if 'tick_volume' in current_raw.dtype.names else 0
            }
            
            previous_raw = rates[1]
            previous_candle = {
                'time': datetime.fromtimestamp(int(previous_raw['time'])),
                'open': float(previous_raw['open']),
                'high': float(previous_raw['high']),
                'low': float(previous_raw['low']),
                'close': float(previous_raw['close']),
                'volume': int(previous_raw['tick_volume']) if 'tick_volume' in previous_raw.dtype.names else 0
            }
            
            # 🔧 IMPROVED: แสดงข้อมูลเปรียบเทียบ
            price_change = current_candle['close'] - previous_candle['close']
            candle_color = 'green' if current_candle['close'] > current_candle['open'] else 'red'
            price_direction = 'higher' if price_change > 0 else 'lower'
            
            print(f"🆕 NEW CANDLE CONFIRMED:")
            print(f"   Time: {current_time.strftime('%H:%M:%S')} (Age: {candle_age_minutes:.1f}m)")
            print(f"   OHLC: {current_candle['open']:.2f}/{current_candle['high']:.2f}/{current_candle['low']:.2f}/{current_candle['close']:.2f}")
            print(f"   Color: {candle_color}")
            print(f"   Direction: {price_direction} ({price_change:+.2f})")
            print(f"   Range: {current_candle['high'] - current_candle['low']:.2f}")
            
            return {
                'current': current_candle,
                'previous': previous_candle,
                'is_new_candle': True,
                'detection_time': datetime.now(),
                'candle_age_minutes': candle_age_minutes,
                'price_change': price_change,
                'candle_color': candle_color
            }
            
        except Exception as e:
            print(f"❌ New candle detection error: {e}")
            return None
    
    def _get_ohlc_data(self) -> Optional[Dict]:
        """
        📊 ดึงข้อมูล OHLC แท่งที่ปิดแล้วเท่านั้น - FIXED TIME CALCULATION
        
        Returns:
            Dict: ข้อมูล current (แท่งที่ปิดล่าสุด) และ previous candle
        """
        try:
            # 🔧 FIXED: ดึงข้อมูล 3 แท่งล่าสุด แต่ข้าม index 0 (แท่งปัจจุบันที่ยังไม่ปิด)
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 1, 2)  # เริ่มจาก index 1, เอา 2 แท่ง
            
            if rates is None or len(rates) < 2:
                print(f"❌ Cannot get sufficient closed candle data for {self.symbol}")
                return None
            
            # แปลง numpy array เป็น dict - ใช้แท่งที่ปิดแล้วเท่านั้น
            current_raw = rates[0]  # แท่งที่ปิดล่าสุด
            current_candle = {
                'time': datetime.fromtimestamp(int(current_raw['time'])),
                'open': float(current_raw['open']),
                'high': float(current_raw['high']),
                'low': float(current_raw['low']),
                'close': float(current_raw['close']),
                'volume': int(current_raw['tick_volume']) if 'tick_volume' in current_raw.dtype.names else 0
            }
            
            previous_raw = rates[1]  # แท่งก่อนหน้า
            previous_candle = {
                'time': datetime.fromtimestamp(int(previous_raw['time'])),
                'open': float(previous_raw['open']),
                'high': float(previous_raw['high']),
                'low': float(previous_raw['low']),
                'close': float(previous_raw['close']),
                'volume': int(previous_raw['tick_volume']) if 'tick_volume' in previous_raw.dtype.names else 0
            }
            
            # 🔧 FIXED: การคำนวณเวลาแท่งปิด - ลบการเช็คที่ไม่จำเป็น
            now = datetime.now()
            
            # เช็คว่าแท่งนี้เก่าเกินไปหรือไม่ (เก่ากว่า 10 นาที = ไม่ current)
            candle_age_minutes = (now - current_candle['time']).total_seconds() / 60
            
            # 🔧 FIXED: ไม่ต้องรอแท่งปิด เพราะเราดึงแท่งที่ปิดแล้วมา
            # แค่เช็คว่าข้อมูลไม่เก่าเกินไป
            if candle_age_minutes > 15:  # ถ้าข้อมูลเก่ากว่า 15 นาที
                print(f"⚠️ Candle data too old: {candle_age_minutes:.1f} minutes")
                return None
            
            print(f"📊 Using CLOSED candles (Age: {candle_age_minutes:.1f}m):")
            print(f"   Current: ${current_candle['close']:.2f} at {current_candle['time'].strftime('%H:%M:%S')}")
            print(f"   Previous: ${previous_candle['close']:.2f} at {previous_candle['time'].strftime('%H:%M:%S')}")
            
            # คำนวณการเปลี่ยนแปลงราคา
            price_change = current_candle['close'] - previous_candle['close']
            price_change_pips = price_change * 100  # สำหรับทองคำ
            
            print(f"   Price change: {price_change:+.2f} ({price_change_pips:+.1f} pips)")
            
            return {
                'current': current_candle,
                'previous': previous_candle,
                'timestamp': datetime.now(),
                'is_closed_candle': True,
                'candle_age_minutes': candle_age_minutes
            }
            
        except Exception as e:
            print(f"❌ OHLC closed data error: {e}")
            return None
            
    def _analyze_candlestick(self, current: Dict, previous: Dict) -> Dict:
        """
        🕯️ วิเคราะห์แท่งเทียนปัจจุบัน - IMPROVED ACCURACY
        
        Args:
            current: ข้อมูลแท่งปัจจุบัน
            previous: ข้อมูลแท่งก่อนหน้า
            
        Returns:
            Dict: ผลการวิเคราะห์แท่งเทียนที่แม่นยำ
        """
        try:
            o, h, l, c = current['open'], current['high'], current['low'], current['close']
            prev_close = previous['close']
            prev_open = previous['open']
            prev_high = previous['high']
            prev_low = previous['low']
            
            # 🔧 IMPROVED: คำนวณขนาดต่างๆ แบบแม่นยำ
            candle_range = h - l
            body_size = abs(c - o)
            
            # ป้องกัน division by zero
            body_ratio = body_size / candle_range if candle_range > 0.001 else 0
            
            # 🔧 IMPROVED: กำหนดสีแท่งเทียนแบบแม่นยำ
            price_threshold = 0.001  # 0.1 pips สำหรับทองคำ
            
            if c > o + price_threshold:
                candle_color = 'green'  # bullish
            elif c < o - price_threshold:
                candle_color = 'red'    # bearish
            else:
                candle_color = 'doji'   # เกือบเท่ากัน
            
            # 🔧 IMPROVED: ทิศทางราคาแบบแม่นยำ
            price_change = c - prev_close
            if abs(price_change) < price_threshold:
                price_direction = 'same_close'
            elif price_change > 0:
                price_direction = 'higher_close'
            else:
                price_direction = 'lower_close'
            
            # 🔧 IMPROVED: คำนวณ wicks แบบถูกต้อง
            if candle_color == 'green':
                upper_wick = h - c
                lower_wick = o - l
                body_top = c
                body_bottom = o
            elif candle_color == 'red':
                upper_wick = h - o
                lower_wick = c - l
                body_top = o
                body_bottom = c
            else:  # doji
                body_mid = (o + c) / 2
                upper_wick = h - max(o, c)
                lower_wick = min(o, c) - l
                body_top = max(o, c)
                body_bottom = min(o, c)
            
            # 🔧 IMPROVED: คำนวณ wick ratios
            upper_wick_ratio = upper_wick / candle_range if candle_range > 0 else 0
            lower_wick_ratio = lower_wick / candle_range if candle_range > 0 else 0
            
            # 🔧 IMPROVED: เพิ่มการวิเคราะห์ momentum
            momentum_score = self._calculate_momentum(current, previous)
            
            # 🔧 IMPROVED: Pattern recognition ที่แม่นยำขึ้น
            pattern_info = self._recognize_advanced_patterns({
                'color': candle_color,
                'body_ratio': body_ratio,
                'upper_wick': upper_wick,
                'lower_wick': lower_wick,
                'upper_wick_ratio': upper_wick_ratio,
                'lower_wick_ratio': lower_wick_ratio,
                'candle_range': candle_range,
                'body_size': body_size,
                'momentum': momentum_score,
                'price_change': price_change
            })
            
            # 🔧 IMPROVED: เพิ่มการวิเคราะห์ relative strength
            relative_strength = self._calculate_relative_strength(current, previous)
            
            analysis_result = {
                'color': candle_color,
                'body_ratio': round(body_ratio, 4),
                'price_direction': price_direction,
                'range': round(candle_range, 4),
                'body_size': round(body_size, 4),
                'upper_wick': round(upper_wick, 4),
                'lower_wick': round(lower_wick, 4),
                'upper_wick_ratio': round(upper_wick_ratio, 4),
                'lower_wick_ratio': round(lower_wick_ratio, 4),
                
                # 🔧 IMPROVED: เพิ่มข้อมูลที่แม่นยำขึ้น
                'price_change': round(price_change, 4),
                'price_change_pips': round(price_change * 100, 2),  # สำหรับทองคำ
                'momentum_score': momentum_score,
                'relative_strength': relative_strength,
                
                # Pattern recognition
                'pattern_name': pattern_info['name'],
                'pattern_strength': pattern_info['strength'],
                'pattern_reliability': pattern_info['reliability'],
                'reversal_pattern': pattern_info['is_reversal'],
                'continuation_pattern': pattern_info['is_continuation'],
                
                # Quality metrics
                'analysis_quality': self._calculate_candle_quality(body_ratio, candle_range, upper_wick_ratio, lower_wick_ratio),
                'signal_clarity': self._calculate_signal_clarity(candle_color, price_direction, body_ratio)
            }
            
            print(f"🕯️ Advanced analysis: {candle_color} candle, body {body_ratio:.3f}, momentum {momentum_score:.2f}")
            
            # บันทึก cache
            self.cached_analysis = analysis_result.copy()
            self.last_analysis_time = datetime.now()
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Candlestick analysis error: {e}")
            return self._get_fallback_analysis()
    
    def _calculate_momentum(self, current: Dict, previous: Dict) -> float:
        """
        🚀 คำนวณ Momentum Score - NEW
        
        Args:
            current: แท่งปัจจุบัน
            previous: แท่งก่อนหน้า
            
        Returns:
            float: Momentum score (-1.0 ถึง 1.0)
        """
        try:
            curr_close = current['close']
            curr_open = current['open'] 
            prev_close = previous['close']
            prev_open = previous['open']
            
            # คำนวณ momentum จากการเปลี่ยนแปลงราคา
            current_move = curr_close - curr_open
            previous_move = prev_close - prev_open
            price_acceleration = curr_close - prev_close
            
            # Normalize momentum 
            curr_range = current['high'] - current['low']
            prev_range = previous['high'] - previous['low']
            avg_range = (curr_range + prev_range) / 2
            
            if avg_range > 0:
                momentum = price_acceleration / avg_range
                # จำกัดในช่วง -1.0 ถึง 1.0
                momentum = max(-1.0, min(1.0, momentum))
            else:
                momentum = 0.0
            
            return round(momentum, 3)
            
        except Exception as e:
            return 0.0

    def _calculate_relative_strength(self, current: Dict, previous: Dict) -> float:
        """
        💪 คำนวณ Relative Strength - NEW
        
        Args:
            current: แท่งปัจจุบัน
            previous: แท่งก่อนหน้า
            
        Returns:
            float: Relative strength (0.0 ถึง 1.0)
        """
        try:
            curr_range = current['high'] - current['low']
            prev_range = previous['high'] - previous['low']
            
            curr_body = abs(current['close'] - current['open'])
            prev_body = abs(previous['close'] - previous['open'])
            
            # เปรียบเทียบขนาด range และ body
            range_ratio = curr_range / prev_range if prev_range > 0 else 1.0
            body_ratio = curr_body / prev_body if prev_body > 0 else 1.0
            
            # คำนวณ relative strength
            relative_strength = (range_ratio + body_ratio) / 2
            
            # Normalize ให้อยู่ในช่วง 0-1
            relative_strength = min(relative_strength / 2, 1.0)  # หารด้วย 2 เพื่อ normalize
            
            return round(relative_strength, 3)
            
        except Exception as e:
            return 0.5

    def _recognize_advanced_patterns(self, candle_data: Dict) -> Dict:
        """
        🔍 จำแนก Candlestick Patterns ขั้นสูง - IMPROVED
        
        Args:
            candle_data: ข้อมูลแท่งเทียนที่คำนวณแล้ว
            
        Returns:
            Dict: ข้อมูล pattern ที่ละเอียด
        """
        try:
            color = candle_data.get('color', '')
            body_ratio = candle_data.get('body_ratio', 0)
            upper_wick_ratio = candle_data.get('upper_wick_ratio', 0)
            lower_wick_ratio = candle_data.get('lower_wick_ratio', 0)
            momentum = candle_data.get('momentum', 0)
            
            pattern_name = 'standard'
            pattern_strength = 0.5
            reliability = 0.5
            is_reversal = False
            is_continuation = False
            
            # 🔧 IMPROVED: Doji Patterns (รายละเอียดขึ้น)
            if body_ratio < 0.05:  # Doji threshold
                if upper_wick_ratio > 0.4 and lower_wick_ratio < 0.1:
                    pattern_name = 'gravestone_doji'
                    pattern_strength = 0.8
                    reliability = 0.75
                    is_reversal = True
                elif lower_wick_ratio > 0.4 and upper_wick_ratio < 0.1:
                    pattern_name = 'dragonfly_doji'
                    pattern_strength = 0.8
                    reliability = 0.75
                    is_reversal = True
                elif upper_wick_ratio > 0.3 and lower_wick_ratio > 0.3:
                    pattern_name = 'long_legged_doji'
                    pattern_strength = 0.6
                    reliability = 0.6
                    is_reversal = True
                else:
                    pattern_name = 'classic_doji'
                    pattern_strength = 0.5
                    reliability = 0.5
                    is_reversal = True
            
            # 🔧 IMPROVED: Hammer & Shooting Star (แม่นยำขึ้น)
            elif body_ratio >= 0.2 and body_ratio <= 0.4:  # Body ปานกลาง
                if color == 'green' and lower_wick_ratio > 0.5 and upper_wick_ratio < 0.1:
                    pattern_name = 'hammer_bullish'
                    pattern_strength = 0.85
                    reliability = 0.8
                    is_reversal = True
                elif color == 'red' and upper_wick_ratio > 0.5 and lower_wick_ratio < 0.1:
                    pattern_name = 'shooting_star'
                    pattern_strength = 0.85
                    reliability = 0.8
                    is_reversal = True
                elif color == 'green' and upper_wick_ratio > 0.5 and lower_wick_ratio < 0.1:
                    pattern_name = 'inverted_hammer'
                    pattern_strength = 0.7
                    reliability = 0.65
                    is_reversal = True
                elif color == 'red' and lower_wick_ratio > 0.5 and upper_wick_ratio < 0.1:
                    pattern_name = 'hanging_man'
                    pattern_strength = 0.7
                    reliability = 0.65
                    is_reversal = True
            
            # 🔧 IMPROVED: Strong Trend Candles (ปรับปรุงการตัดสิน)
            elif body_ratio > 0.6:  # Strong body
                if color == 'green':
                    if momentum > 0.5:
                        pattern_name = 'strong_bullish_momentum'
                        pattern_strength = 0.9
                        reliability = 0.8
                        is_continuation = True
                    else:
                        pattern_name = 'strong_bullish'
                        pattern_strength = 0.75
                        reliability = 0.7
                        is_continuation = True
                elif color == 'red':
                    if momentum < -0.5:
                        pattern_name = 'strong_bearish_momentum'
                        pattern_strength = 0.9
                        reliability = 0.8
                        is_continuation = True
                    else:
                        pattern_name = 'strong_bearish'
                        pattern_strength = 0.75
                        reliability = 0.7
                        is_continuation = True
            
            # 🔧 IMPROVED: Spinning Tops & Small Bodies
            elif body_ratio >= 0.05 and body_ratio <= 0.2:  # Small body
                if upper_wick_ratio > 0.3 and lower_wick_ratio > 0.3:
                    pattern_name = 'spinning_top'
                    pattern_strength = 0.4
                    reliability = 0.5
                    is_reversal = True
                else:
                    pattern_name = 'small_body'
                    pattern_strength = 0.3
                    reliability = 0.4
            
            # 🔧 IMPROVED: Medium Body Candles
            else:  # body_ratio 0.2-0.6
                if color == 'green':
                    if lower_wick_ratio > 0.3:
                        pattern_name = 'bullish_with_support'
                        pattern_strength = 0.65
                        reliability = 0.6
                    else:
                        pattern_name = 'medium_bullish'
                        pattern_strength = 0.6
                        reliability = 0.55
                elif color == 'red':
                    if upper_wick_ratio > 0.3:
                        pattern_name = 'bearish_with_resistance'
                        pattern_strength = 0.65
                        reliability = 0.6
                    else:
                        pattern_name = 'medium_bearish'
                        pattern_strength = 0.6
                        reliability = 0.55
                else:
                    pattern_name = 'neutral_medium'
                    pattern_strength = 0.4
                    reliability = 0.4
            
            # 🔧 IMPROVED: ปรับ strength ตาม momentum
            if abs(momentum) > 0.3:
                pattern_strength *= (1 + abs(momentum) * 0.2)  # เพิ่ม 20% สำหรับ momentum แรง
                pattern_strength = min(pattern_strength, 0.95)  # จำกัดไม่เกิน 95%
            
            return {
                'name': pattern_name,
                'strength': round(pattern_strength, 3),
                'reliability': round(reliability, 3),
                'is_reversal': is_reversal,
                'is_continuation': is_continuation,
                'body_ratio': round(body_ratio, 4),
                'upper_wick_ratio': round(upper_wick_ratio, 4),
                'lower_wick_ratio': round(lower_wick_ratio, 4),
                'momentum_adjusted': abs(momentum) > 0.3
            }
            
        except Exception as e:
            print(f"❌ Advanced pattern recognition error: {e}")
            return {
                'name': 'error',
                'strength': 0.0,
                'reliability': 0.0,
                'is_reversal': False,
                'is_continuation': False,
                'body_ratio': 0,
                'upper_wick_ratio': 0,
                'lower_wick_ratio': 0,
                'momentum_adjusted': False
            }

    def _calculate_candle_quality(self, body_ratio: float, candle_range: float, 
                                upper_wick_ratio: float, lower_wick_ratio: float) -> float:
        """
        🎯 คำนวณคุณภาพของแท่งเทียน - IMPROVED ACCURACY
        
        Args:
            body_ratio: สัดส่วน body
            candle_range: ขนาดแท่งเทียน
            upper_wick_ratio: สัดส่วน upper wick
            lower_wick_ratio: สัดส่วน lower wick
            
        Returns:
            float: คะแนนคุณภาพ 0-1
        """
        try:
            # 🔧 IMPROVED: คะแนนจาก body ratio (แม่นยำขึ้น)
            if body_ratio >= 0.7:  # body แข็งแกร่งมาก
                ratio_score = 1.0
            elif body_ratio >= 0.5:  # body แข็งแกร่ง
                ratio_score = 0.9
            elif body_ratio >= 0.3:  # body ปานกลาง
                ratio_score = 0.7
            elif body_ratio >= 0.15:  # body อ่อน
                ratio_score = 0.5
            elif body_ratio >= 0.05:  # body เล็ก
                ratio_score = 0.3
            else:  # doji หรือ body เล็กมาก
                ratio_score = 0.4  # doji อาจมีความหมายพิเศษ
            
            # 🔧 IMPROVED: คะแนนจาก candle range (ความผันผวน)
            if candle_range >= 8.0:  # แท่งใหญ่มาก (สำหรับทองคำ)
                range_score = 1.0
            elif candle_range >= 5.0:  # แท่งใหญ่
                range_score = 0.9
            elif candle_range >= 3.0:  # แท่งปานกลาง
                range_score = 0.8
            elif candle_range >= 1.5:  # แท่งเล็ก
                range_score = 0.6
            elif candle_range >= 0.8:  # แท่งเล็กมาก
                range_score = 0.4
            else:  # แท่งแคบมาก
                range_score = 0.2
            
            # 🔧 IMPROVED: คะแนนจาก wick balance
            wick_balance = abs(upper_wick_ratio - lower_wick_ratio)
            if wick_balance < 0.1:  # wicks สมดุล
                balance_score = 1.0
            elif wick_balance < 0.3:  # wicks ค่อนข้างสมดุล
                balance_score = 0.8
            elif wick_balance < 0.5:  # wicks ไม่สมดุลเล็กน้อย
                balance_score = 0.6
            else:  # wicks ไม่สมดุลมาก (อาจเป็น reversal pattern)
                balance_score = 0.7  # ให้คะแนนกลางๆ เพราะอาจมีความหมาย
            
            # 🔧 IMPROVED: รวมคะแนน (ปรับ weight ใหม่)
            final_score = (
                ratio_score * 0.5 +      # body สำคัญที่สุด
                range_score * 0.3 +      # range สำคัญรอง
                balance_score * 0.2      # balance เสริม
            )
            
            return round(final_score, 3)
            
        except Exception as e:
            print(f"❌ Candle quality calculation error: {e}")
            return 0.5

    def _calculate_signal_clarity(self, candle_color: str, price_direction: str, body_ratio: float) -> float:
        """
        🎯 คำนวณความชัดเจนของ Signal - NEW
        
        Args:
            candle_color: สีแท่งเทียน
            price_direction: ทิศทางราคา
            body_ratio: สัดส่วน body
            
        Returns:
            float: Signal clarity score (0.0 ถึง 1.0)
        """
        try:
            clarity_score = 0.0
            
            # ความสอดคล้องระหว่างสีและทิศทาง
            if (candle_color == 'green' and price_direction == 'higher_close') or \
               (candle_color == 'red' and price_direction == 'lower_close'):
                clarity_score += 0.6  # สอดคล้องกัน
            elif candle_color == 'doji':
                clarity_score += 0.3  # neutral
            else:
                clarity_score += 0.1  # ไม่สอดคล้อง
            
            # ความชัดเจนจาก body size
            if body_ratio >= 0.5:
                clarity_score += 0.4  # signal ชัดเจน
            elif body_ratio >= 0.2:
                clarity_score += 0.3  # signal ปานกลาง
            elif body_ratio >= 0.05:
                clarity_score += 0.2  # signal อ่อน
            else:
                clarity_score += 0.1  # signal คลุมเครือ
            
            return round(min(clarity_score, 1.0), 3)
            
        except Exception as e:
            return 0.5
        
    def _calculate_signal_clarity(self, candle_color: str, price_direction: str, body_ratio: float) -> float:
        """
        🎯 คำนวณความชัดเจนของ Signal - NEW
        
        Args:
            candle_color: สีแท่งเทียน
            price_direction: ทิศทางราคา
            body_ratio: สัดส่วน body
            
        Returns:
            float: Signal clarity score (0.0 ถึง 1.0)
        """
        try:
            clarity_score = 0.0
            
            # ความสอดคล้องระหว่างสีและทิศทาง
            if (candle_color == 'green' and price_direction == 'higher_close') or \
               (candle_color == 'red' and price_direction == 'lower_close'):
                clarity_score += 0.6  # สอดคล้องกัน
            elif candle_color == 'doji':
                clarity_score += 0.3  # neutral
            else:
                clarity_score += 0.1  # ไม่สอดคล้อง
            
            # ความชัดเจนจาก body size
            if body_ratio >= 0.5:
                clarity_score += 0.4  # signal ชัดเจน
            elif body_ratio >= 0.2:
                clarity_score += 0.3  # signal ปานกลาง
            elif body_ratio >= 0.05:
                clarity_score += 0.2  # signal อ่อน
            else:
                clarity_score += 0.1  # signal คลุมเครือ
            
            return round(min(clarity_score, 1.0), 3)
            
        except Exception as e:
            return 0.5
        
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
        """🔧 ตรวจสอบ Cache - ปรับให้เหมาะกับ real-time"""
        try:
            if self.cached_analysis is None:
                return False
            
            # 🔧 NEW: Cache valid นานขึ้นสำหรับแท่งที่ปิดแล้ว
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