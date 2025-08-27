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
                
        # NEW: ใช้ sequence tracking แทน time tracking
        self.last_candle_signature = None  # ลายเซ็นของแท่งล่าสุด (OHLC + time)
        self.processed_signatures = set()  # เก็บลายเซ็นที่ประมวลผลแล้ว
        self.max_signature_history = 50
        print(f"🕯️ Real-time Candlestick Analyzer initialized for {self.symbol}")
        print(f"   Will detect new candles immediately upon close")
    
    # ==========================================
    # 📊 MAIN ANALYSIS METHODS
    # ==========================================
    
    def _get_latest_closed_candle(self) -> Optional[Dict]:
        """
        📊 Real Candle Comparison - ใช้แท่งจริงจาก MT5
        
        🔧 BACK TO BASICS:
        - ใช้แท่งจริงจาก Chart
        - rates[0] = แท่งที่ปิดล่าสุด
        - rates[1] = แท่งก่อนหน้า
        - เปรียบเทียบ: rates[0].close vs rates[1].close
        - ไม่สร้างแท่งปลอม ใช้ของจริงเท่านั้น
        """
        try:
            print(f"🔍 Getting REAL candles for symbol: {self.symbol}")
            
            # 1. ตรวจสอบการเชื่อมต่อ MT5
            if not self.mt5_connector or not self.mt5_connector.is_connected:
                print("❌ MT5 not connected")
                return None
            
            # 2. ดึงแท่งเทียน 3 แท่งล่าสุดจาก MT5 (ต้องการ rates[1] และ rates[2])
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 3)
            if rates is None or len(rates) < 3:
                print(f"❌ Cannot get 3 candles for symbol: {self.symbol}")
                # ลอง symbol อื่น
                alternative_symbols = ["XAUUSD", "GOLD", "XAUUSD.cmd"]
                for alt_symbol in alternative_symbols:
                    print(f"🔄 Trying alternative symbol: {alt_symbol}")
                    rates = mt5.copy_rates_from_pos(alt_symbol, self.timeframe, 0, 3)
                    if rates is not None and len(rates) >= 3:
                        print(f"✅ Found candle data with symbol: {alt_symbol}")
                        self.symbol = alt_symbol  # อัพเดท symbol
                        break
                
                if rates is None or len(rates) < 3:
                    print("❌ No real candle data available")
                    return None
            
            print(f"✅ Got {len(rates)} real candles from MT5")
            
            # 3. แท่งจริงจาก MT5 - ใช้ rates[1] vs rates[2]
            current_raw = rates[1]    # แท่งที่เพิ่งปิด (เสถียรแล้ว)
            previous_raw = rates[2]   # แท่งก่อนหน้า (ปิดแล้ว)
            
            # 4. แปลงข้อมูลแท่งปัจจุบัน
            current_candle = {
                'time': datetime.fromtimestamp(int(current_raw['time'])),
                'open': float(current_raw['open']),
                'high': float(current_raw['high']),
                'low': float(current_raw['low']),
                'close': float(current_raw['close']),
                'volume': int(current_raw['tick_volume']) if 'tick_volume' in current_raw.dtype.names else 0
            }
            
            # 5. แปลงข้อมูลแท่งก่อนหน้า
            previous_candle = {
                'time': datetime.fromtimestamp(int(previous_raw['time'])),
                'open': float(previous_raw['open']),
                'high': float(previous_raw['high']),
                'low': float(previous_raw['low']),
                'close': float(previous_raw['close']),
                'volume': int(previous_raw['tick_volume']) if 'tick_volume' in previous_raw.dtype.names else 0
            }
            
            # 6. Debug ข้อมูลแท่งจริง - rates[1] vs rates[2]
            print(f"📊 REAL CANDLE COMPARISON (rates[1] vs rates[2]):")
            print(f"   Current Candle [rates[1] - {current_candle['time'].strftime('%H:%M')}]:")
            print(f"     OHLC: {current_candle['open']:.2f}/{current_candle['high']:.2f}/{current_candle['low']:.2f}/{current_candle['close']:.2f}")
            print(f"   Previous Candle [rates[2] - {previous_candle['time'].strftime('%H:%M')}]:")
            print(f"     OHLC: {previous_candle['open']:.2f}/{previous_candle['high']:.2f}/{previous_candle['low']:.2f}/{previous_candle['close']:.2f}")
            
            # 7. คำนวณการเปลี่ยนแปลงราคา
            price_diff = current_candle['close'] - previous_candle['close']
            
            print(f"   Price Difference: {price_diff:+.2f}")
            
            # 8. กำหนดทิศทางการเทรดจากแท่งจริง rates[1] vs rates[2]
            min_price_change = 0.10  # ลดลงเป็น 10 cents สำหรับแท่งจริง
            
            if price_diff > min_price_change:
                signal_direction = 'BUY_SIGNAL'
                print(f"   → 🟢 BUY Signal: rates[1] Close > rates[2] Close (+{price_diff:.2f})")
            elif price_diff < -min_price_change:
                signal_direction = 'SELL_SIGNAL'
                print(f"   → 🔴 SELL Signal: rates[1] Close < rates[2] Close ({price_diff:.2f})")
            else:
                signal_direction = 'NO_SIGNAL'
                print(f"   → ⏳ No Signal: Change too small ({price_diff:+.2f})")
            
            # 9. คำนวณความแข็งแกร่งจากแท่งจริง
            candle_range = current_candle['high'] - current_candle['low']
            body_size = abs(current_candle['close'] - current_candle['open'])
            body_ratio = body_size / candle_range if candle_range > 0 else 0
            
            # รวม price strength และ candle strength
            price_strength = min(abs(price_diff) / 5.0, 1.0)  # normalize by 5.0
            candle_strength = min(body_ratio * 2, 1.0)
            overall_strength = (price_strength + candle_strength) / 2
            
            print(f"   💪 Candle Analysis:")
            print(f"     Body Ratio: {body_ratio:.3f}")
            print(f"     Price Strength: {price_strength:.3f}")
            print(f"     Overall Strength: {overall_strength:.3f}")
            
            return {
                'current': current_candle,
                'previous': previous_candle,
                'signal_direction': signal_direction,
                'price_difference': price_diff,
                'price_strength': price_strength,
                'candle_strength': candle_strength,
                'overall_strength': overall_strength,
                'body_ratio': body_ratio,
                'analysis_method': 'real_candle_rates_1_vs_2'
            }
            
        except Exception as e:
            print(f"❌ Real candle comparison error: {e}")
            return None
            
    def get_current_analysis(self) -> Optional[Dict]:
        """
        📊 Real Candle Analysis - ใช้แท่งจริงจาก MT5
        
        🔧 BACK TO REAL CANDLES:
        - BUY: Current Close > Previous Close
        - SELL: Current Close < Previous Close
        - ใช้แท่งจริงจาก Chart
        - ไม่สร้างข้อมูลปลอม
        """
        try:
            print("=== 📊 REAL CANDLE ANALYSIS ===")
            
            if not self.mt5_connector.is_connected:
                print("❌ MT5 not connected")
                return None
            
            # ดึงข้อมูลแท่งจริงจาก MT5
            candle_data = self._get_latest_closed_candle()
            if not candle_data:
                print("❌ No real candle data available")
                return None
            
            current_candle = candle_data['current']
            previous_candle = candle_data['previous']
            
            # สร้าง OHLC signature จากแท่งจริง
            candle_signature = self._create_candle_signature(current_candle)
            
            # เช็คว่าวิเคราะห์แท่งนี้แล้วหรือยัง
            if self._is_signature_processed(candle_signature):
                print("🔄 Real candle already analyzed - skipping")
                return None
            
            print(f"🆕 NEW REAL CANDLE ANALYSIS (rates[1] vs rates[2]):")
            print(f"   OHLC Signature: {candle_signature}")
            print(f"   Method: Real Candle rates[1] vs rates[2] Comparison")
            
            # ดึงข้อมูลจากแท่งจริง
            current_close = current_candle['close']
            previous_close = previous_candle['close']
            price_diff = candle_data['price_difference']
            overall_strength = candle_data['overall_strength']
            body_ratio = candle_data['body_ratio']
            
            # กำหนดสีแท่งเทียนจากข้อมูลจริง
            if current_candle['close'] > current_candle['open']:
                candle_color = 'green'
                candle_type = 'bullish'
            elif current_candle['close'] < current_candle['open']:
                candle_color = 'red'
                candle_type = 'bearish'
            else:
                candle_color = 'doji'
                candle_type = 'neutral'
            
            # กำหนดทิศทางราคา
            if current_close > previous_close:
                price_direction = 'higher_close'
                signal_type = 'bullish'
            elif current_close < previous_close:
                price_direction = 'lower_close'
                signal_type = 'bearish'
            else:
                price_direction = 'same_close'
                signal_type = 'neutral'
            
            print(f"📊 REAL CANDLE RESULTS:")
            print(f"   Current Close: ${current_close:.2f}")
            print(f"   Previous Close: ${previous_close:.2f}")
            print(f"   Price Change: {price_diff:+.2f}")
            print(f"   Candle Color: {candle_color}")
            print(f"   Signal Type: {signal_type}")
            print(f"   Body Ratio: {body_ratio:.3f}")
            print(f"   Overall Strength: {overall_strength:.3f}")
            
            # รวมข้อมูลทั้งหมดจากแท่งจริง
            complete_analysis = {
                'symbol': self.symbol,
                'timestamp': datetime.now(),
                'candle_time': current_candle['time'],
                'candle_signature': candle_signature,
                
                # Current candle data (จริง)
                'open': current_candle['open'],
                'high': current_candle['high'],
                'low': current_candle['low'],
                'close': current_candle['close'],
                
                # Previous candle data (จริง)
                'previous_open': previous_candle['open'],
                'previous_high': previous_candle['high'],
                'previous_low': previous_candle['low'],
                'previous_close': previous_candle['close'],
                
                # Analysis results จากแท่งจริง
                'price_difference': price_diff,
                'body_ratio': body_ratio,
                'candle_color': candle_color,
                'candle_type': candle_type,
                'price_direction': price_direction,
                'signal_type': signal_type,
                'analysis_strength': overall_strength,
                
                # Pattern info
                'pattern_name': f'real_{signal_type}',
                'pattern_strength': overall_strength,
                
                # Technical indicators
                'is_bullish': signal_type == 'bullish',
                'is_bearish': signal_type == 'bearish',
                'is_strong_signal': overall_strength >= 0.3,
                
                # Volume จากแท่งจริง
                'volume_available': True,
                'current_volume': current_candle['volume'],
                'previous_volume': previous_candle['volume'],
                'volume_factor': current_candle['volume'] / max(previous_candle['volume'], 1),
                
                # Metadata
                'tracking_method': 'real_candle_rates_1_vs_2',
                'market_context': f"real_session_{datetime.now().hour}",
                'analysis_method': 'mt5_rates_1_vs_2',
                'candle_range': current_candle['high'] - current_candle['low'],
                'body_size': abs(current_candle['close'] - current_candle['open']),
                'price_strength': candle_data['price_strength'],
                'candle_strength': candle_data['candle_strength']
            }
            
            # บันทึกว่าวิเคราะห์แท่งจริงนี้แล้ว
            self._mark_signature_processed(candle_signature)
            
            print(f"✅ REAL CANDLE ANALYSIS COMPLETED")
            print(f"   Signal: {signal_type.upper()}")
            print(f"   Strength: {overall_strength:.3f}")
            print(f"   Real OHLC: {candle_signature}")
            
            return complete_analysis
            
        except Exception as e:
            print(f"❌ Real candle analysis error: {e}")
            return None
                        
    def _create_candle_signature(self, candle: Dict) -> str:
        """
        🔑 สร้างลายเซ็น OHLC - PURE OHLC NO TIME VERSION
        
        🔧 FINAL VERSION: ไม่ใช้เวลาเลย ใช้แค่ OHLC
        - ไม่มี timestamp
        - ไม่มี datetime
        - แค่ราคา 4 ตัวเท่านั้น
        """
        try:
            # ดึงข้อมูล OHLC และปัดเศษ 2 ตำแหน่ง
            o = round(float(candle['open']), 2)
            h = round(float(candle['high']), 2)
            l = round(float(candle['low']), 2)
            c = round(float(candle['close']), 2)
            
            # สร้างลายเซ็นจาก OHLC เท่านั้น - ไม่มีเวลา
            signature = f"{o}_{h}_{l}_{c}"
            
            print(f"🔑 PURE OHLC Signature: {signature}")
            
            return signature
            
        except Exception as e:
            print(f"❌ OHLC signature error: {e}")
            # Fallback signature แบบไม่ใช้เวลา
            return f"error_{hash(str(candle))}"

    def _is_signature_processed(self, signature: str) -> bool:
        """
        🔍 เช็คว่าลายเซ็น OHLC นี้ประมวลผลแล้วหรือยัง
        
        Args:
            signature: ลายเซ็น OHLC
            
        Returns:
            bool: True ถ้าประมวลผลแล้ว
        """
        is_processed = signature in self.processed_signatures
        
        if is_processed:
            print(f"✅ OHLC Signature already processed: {signature}")
        else:
            print(f"🆕 New OHLC Signature: {signature}")
        
        return is_processed

    def _mark_signature_processed(self, signature: str):
        """
        ✅ บันทึกลายเซ็น OHLC ว่าประมวลผลแล้ว - NO TIME VERSION
        """
        try:
            self.processed_signatures.add(signature)
            
            # เก็บแค่ 20 ลายเซ็นล่าสุด (ลดลงเพราะไม่มี timestamp)
            if len(self.processed_signatures) > 20:
                # ลบแบบ FIFO - เอาตัวแรกออก
                oldest_signature = next(iter(self.processed_signatures))
                self.processed_signatures.remove(oldest_signature)
                print(f"🗑️ Removed oldest OHLC: {oldest_signature}")
            
            print(f"✅ OHLC Signature processed: {signature}")
            print(f"   Total processed: {len(self.processed_signatures)}")
            
        except Exception as e:
            print(f"❌ Mark signature error: {e}")

    def _extract_timestamp_from_signature(self, signature: str) -> float:
        """
        🔧 DEPRECATED: ไม่ใช้ timestamp ใน signature แล้ว
        
        🚫 Method นี้ไม่ถูกใช้แล้วเพราะเปลี่ยนเป็น OHLC-only signature
        เก็บไว้เพื่อ backward compatibility เท่านั้น
        
        Args:
            signature: ลายเซ็น OHLC
            
        Returns:
            float: timestamp ปัจจุบัน (fallback)
        """
        print(f"⚠️ WARNING: _extract_timestamp_from_signature is deprecated")
        print(f"   OHLC signatures don't contain timestamps anymore")
        print(f"   Returning current timestamp as fallback")
        
        # Return current time as fallback
        return datetime.now().timestamp()
            

    def _analyze_candlestick(self, current: Dict, previous: Dict) -> Dict:
        """
        🕯️ วิเคราะห์แท่งเทียน - IMPROVED WITH FIXED DATA
        """
        try:
            # 🔧 FIXED: ใช้ข้อมูลที่ถูกต้อง
            o, h, l, c = current['open'], current['high'], current['low'], current['close']
            prev_close = previous['close']
            prev_open = previous['open']
            prev_high = previous['high']
            prev_low = previous['low']
            
            print(f"🕯️ === CANDLESTICK ANALYSIS (FIXED) ===")
            print(f"   Current OHLC: {o:.4f}/{h:.4f}/{l:.4f}/{c:.4f}")
            print(f"   Previous OHLC: {prev_open:.4f}/{prev_high:.4f}/{prev_low:.4f}/{prev_close:.4f}")
            
            # คำนวณขนาดต่างๆ
            candle_range = h - l
            body_size = abs(c - o)
            
            # ป้องกัน division by zero
            body_ratio = body_size / candle_range if candle_range > 0.0001 else 0
            
            # กำหนดสีแท่งเทียน
            price_threshold = 0.0001  # threshold สำหรับทองคำ
            
            if c > o + price_threshold:
                candle_color = 'green'  # bullish
            elif c < o - price_threshold:
                candle_color = 'red'    # bearish
            else:
                candle_color = 'doji'   # เกือบเท่ากัน
            
            # ทิศทางราคาเทียบกับแท่งก่อนหน้า
            price_change = c - prev_close
            if abs(price_change) < price_threshold:
                price_direction = 'same_close'
            elif price_change > 0:
                price_direction = 'higher_close'
            else:
                price_direction = 'lower_close'
            
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
            
            # คำนวณ wick ratios
            upper_wick_ratio = upper_wick / candle_range if candle_range > 0 else 0
            lower_wick_ratio = lower_wick / candle_range if candle_range > 0 else 0
            
            # Pattern recognition
            pattern_info = self._recognize_advanced_patterns({
                'color': candle_color,
                'body_ratio': body_ratio,
                'upper_wick': upper_wick,
                'lower_wick': lower_wick,
                'upper_wick_ratio': upper_wick_ratio,
                'lower_wick_ratio': lower_wick_ratio,
                'candle_range': candle_range,
                'body_size': body_size,
                'price_change': price_change
            })
            
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
                'price_change': round(price_change, 4),
                'price_change_pips': round(price_change * 10000, 2),
                'pattern_name': pattern_info['name'],
                'pattern_strength': pattern_info['strength'],
                'pattern_reliability': pattern_info['reliability'],
                'analysis_quality': self._calculate_candle_quality(body_ratio, candle_range, upper_wick_ratio, lower_wick_ratio),
                'signal_clarity': self._calculate_signal_clarity(candle_color, price_direction, body_ratio)
            }
            
            print(f"📊 ANALYSIS RESULTS:")
            print(f"   Color: {candle_color}")
            print(f"   Body Ratio: {body_ratio:.3f} ({body_ratio*100:.1f}%)")
            print(f"   Price Direction: {price_direction}")
            print(f"   Price Change: {price_change:+.4f} ({price_change*10000:+.1f} pips)")
            print(f"   Range: {candle_range:.4f}")
            print(f"   Pattern: {pattern_info['name']}")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Candlestick analysis error: {e}")
            return self._get_fallback_analysis()
        

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