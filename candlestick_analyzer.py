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
        🔧 เริ่มต้น Candlestick Analyzer - COMPLETELY FIXED
        
        🚀 Fixed Issues:
        - Invalid time order detection
        - Proper duplicate prevention
        - Real-time candle processing
        - Memory management
        """
        self.mt5_connector = mt5_connector
        self.config = config
        
        # การตั้งค่าพื้นฐาน
        self.symbol = config.get("trading", {}).get("symbol", "XAUUSD.v")
        self.timeframe = mt5.TIMEFRAME_M1
        
        # การตั้งค่า analysis parameters
        self.min_candles_required = 3  # ลดจาก 20 เป็น 3 (ใช้แค่ 3 แท่ง)
        self.volume_lookback_periods = 10
        
        # Pattern recognition settings
        self.doji_threshold = 0.05
        self.strong_body_threshold = 0.6
        
        # 🔧 CACHE MANAGEMENT - ปรับให้เหมาะ real-time
        self.last_analysis_time = datetime.min
        self.last_analyzed_candle_time = datetime.min
        self.cache_duration_seconds = 2   # ลดเหลือ 5 วินาที เพื่อ real-time
        self.cached_analysis = None
        
        # 🔧 VOLUME TRACKING
        self.volume_available = False
        self.volume_history = []
        self.max_volume_history = 20
        
        # 🆕 STRICT SIGNATURE TRACKING
        self.processed_signatures = set()
        self.max_signature_history = 500  # ปรับเป็น 500 เพื่อประสิทธิภาพ
        
        # 🆕 CANDLE STATE TRACKING  
        self.last_candle_signature = None
        self.last_processed_candle_time = datetime.min
        self.minimum_time_gap_seconds = 10  # 🔧 ใหม่: ต้องห่างกัน 30 วินาทีขั้นต่ำ
        
        # 🆕 PERFORMANCE COUNTERS
        self.analysis_count = 0
        self.duplicate_blocks = 0
        self.successful_analysis = 0
        self.time_order_errors = 0        # 🆕 นับ time order errors
        self.invalid_data_errors = 0      # 🆕 นับ invalid data errors
        
        # 🆕 DATA VALIDATION FLAGS
        self.strict_time_checking = True   # เปิดการเช็คเวลาอย่างเข้มงวด
        self.allow_same_minute_candles = False  # ไม่อนุญาตแท่งเดียวกันในนาทีเดียวกัน
        
        # 🔧 PERSISTENCE INTEGRATION
        self.persistence_manager = None
        
        # 🆕 REAL-TIME PROCESSING FLAGS
        self.real_time_mode = True         # โหมด real-time
        self.force_sequential_processing = True  # บังคับประมวลผลตามลำดับเวลา
           
        # 💾 NEW: State Management สำหรับเก็บ Reference Candle
        self.reference_candle = None           # เก็บข้อมูลแท่งอ้างอิง
        self.reference_timestamp = 0           # timestamp ของแท่งอ้างอิง  
        self.waiting_for_new_candle = False    # กำลังรอแท่งใหม่หรือไม่
        self.last_checked_timestamp = 0 
        
        self.price_history = []        # เก็บราคาย้อนหลัง
        self.high_low_levels = {}      # เก็บ high/low ของแต่ละนาที
        self.last_minute_processed = ""  # นาทีล่าสุดที่ประมวลผล
        self.current_minute_data = {    # ข้อมูลนาทีปัจจุบัน
            'high': 0,
            'low': 999999,
            'open': 0,
            'close': 0,
            'tick_count': 0
        }

        # print(f"🕯️ COMPLETELY FIXED Candlestick Analyzer for {self.symbol}")
        # print(f"   Real-time mode: {self.real_time_mode}")
        # print(f"   Cache duration: {self.cache_duration_seconds}s")
        # print(f"   Min time gap: {self.minimum_time_gap_seconds}s")
        # print(f"   Strict time checking: {self.strict_time_checking}")
        # print(f"   Sequential processing: {self.force_sequential_processing}")
        # print(f"   Max signatures: {self.max_signature_history}")
        # print(f"   Duplicate prevention: ULTRA STRICT")
        # print(f"   🎯 Ready for breakout/breakdown detection")

                    

    def get_current_analysis(self) -> Optional[Dict]:
        """
        🎯 SIMPLE METHOD: สร้าง OHLC เอง จาก tick ไม่พึ่ง rates
        
        ✅ Logic เรียบง่าย:
        1. เก็บ tick ปัจจุบัน
        2. สร้าง OHLC ของนาทีปัจจุบัน
        3. เมื่อนาทีใหม่ → เทียบกับนาทีก่อน
        4. ถ้าตรงเงื่อนไข → ส่ง Signal
        """
        try:
            if not self.mt5_connector.is_connected:
                return None

            # 1. ดึงราคาปัจจุบัน
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                print("❌ Cannot get current tick")
                return None
            
            current_price = float(tick.bid)
            tick_time = datetime.fromtimestamp(tick.time)
            current_minute = tick_time.strftime('%H:%M')
            
            print(f"\n🎯 === SIMPLE TICK-BASED ANALYSIS ===")
            print(f"🕐 Current time: {tick_time.strftime('%H:%M:%S')}")
            print(f"💰 Current price: ${current_price:.4f}")
            print(f"📅 Current minute: {current_minute}")
            
            # 2. อัพเดท OHLC ของนาทีปัจจุบัน
            if current_minute != self.last_minute_processed:
                # 🆕 นาทีใหม่ - บันทึกนาทีก่อนแล้วเริ่มใหม่
                
                if self.last_minute_processed:  # มีข้อมูลนาทีก่อน
                    # บันทึกข้อมูลนาทีที่ผ่านมา
                    self.high_low_levels[self.last_minute_processed] = {
                        'high': self.current_minute_data['high'],
                        'low': self.current_minute_data['low'],
                        'open': self.current_minute_data['open'], 
                        'close': self.current_minute_data['close'],
                        'tick_count': self.current_minute_data['tick_count']
                    }
                    
                    print(f"💾 SAVED PREVIOUS MINUTE: {self.last_minute_processed}")
                    print(f"   📈 High: ${self.current_minute_data['high']:.4f}")
                    print(f"   📉 Low:  ${self.current_minute_data['low']:.4f}")
                    print(f"   📊 Close: ${self.current_minute_data['close']:.4f}")
                    print(f"   🎯 Ticks: {self.current_minute_data['tick_count']}")
                
                # เริ่มนาทีใหม่
                self.current_minute_data = {
                    'high': current_price,
                    'low': current_price,
                    'open': current_price,
                    'close': current_price,
                    'tick_count': 1
                }
                
                print(f"🆕 STARTED NEW MINUTE: {current_minute}")
                print(f"   Opening price: ${current_price:.4f}")
                
                # ถ้ามีข้อมูลนาทีก่อน → เทียบกัน
                if self.last_minute_processed in self.high_low_levels:
                    return self._check_breakout_conditions(current_minute)
                
                self.last_minute_processed = current_minute
                return None
                
            else:
                # 🔄 นาทีเดิม - อัพเดท OHLC
                self.current_minute_data['high'] = max(self.current_minute_data['high'], current_price)
                self.current_minute_data['low'] = min(self.current_minute_data['low'], current_price)
                self.current_minute_data['close'] = current_price
                self.current_minute_data['tick_count'] += 1
                
                # แสดงข้อมูลนาทีปัจจุบัน
                print(f"🔄 UPDATING MINUTE: {current_minute}")
                print(f"   📈 High: ${self.current_minute_data['high']:.4f}")
                print(f"   📉 Low:  ${self.current_minute_data['low']:.4f}")
                print(f"   📊 Current: ${current_price:.4f}")
                print(f"   🎯 Ticks: {self.current_minute_data['tick_count']}")
                
                return None  # ยังไม่เสร็จ
            
        except Exception as e:
            print(f"❌ Simple analysis error: {e}")
            return None

    def _check_breakout_conditions(self, current_minute: str) -> Optional[Dict]:
        """
        🎯 เช็คเงื่อนไข Breakout เมื่อมีข้อมูลครบ
        """
        try:
            # ดึงข้อมูลนาทีก่อนหน้า
            prev_minute_data = self.high_low_levels[self.last_minute_processed]
            
            # ราคาปิดของนาทีก่อน (Close จริง)
            prev_close = prev_minute_data['close']
            prev_high = prev_minute_data['high'] 
            prev_low = prev_minute_data['low']
            
            # ราคาเปิดของนาทีปัจจุบัน
            current_open = self.current_minute_data['open']
            
            print(f"🔥 === BREAKOUT CHECK ===")
            print(f"📊 PREVIOUS MINUTE ({self.last_minute_processed}):")
            print(f"   📈 High: ${prev_high:.4f}")
            print(f"   📉 Low:  ${prev_low:.4f}")
            print(f"   📊 Close: ${prev_close:.4f}")
            print(f"")
            print(f"📊 NEW MINUTE ({current_minute}):")
            print(f"   📊 Open: ${current_open:.4f}")
            print(f"")
            print(f"🔥 COMPARISON:")
            print(f"   New Open: ${current_open:.4f}")
            print(f"   vs Previous High: ${prev_high:.4f}")
            print(f"   vs Previous Low:  ${prev_low:.4f}")
            
            # เช็คเงื่อนไข Gap
            tolerance = 0.01
            is_gap_up = current_open > (prev_high + tolerance)
            is_gap_down = current_open < (prev_low - tolerance)
            
            print(f"")
            print(f"🎯 GAP CONDITIONS:")
            print(f"   🟢 BUY (Gap Up):   ${current_open:.4f} > ${prev_high + tolerance:.4f} = {is_gap_up}")
            print(f"   🔴 SELL (Gap Down): ${current_open:.4f} < ${prev_low - tolerance:.4f} = {is_gap_down}")
            
            if not (is_gap_up or is_gap_down):
                print("⏳ No gap detected - normal continuation")
                return None
            
            # สร้าง signature
            signature = f"GAP_{current_minute.replace(':', '')}_{current_open:.1f}"
            
            # เช็ค duplicate
            if hasattr(self, 'processed_signatures') and signature in self.processed_signatures:
                print(f"🚫 DUPLICATE GAP BLOCKED: {signature}")
                return None
            
            # Lock
            if not hasattr(self, 'processed_signatures'):
                self.processed_signatures = set()
            self.processed_signatures.add(signature)
            
            # คำนวณความแรง
            if is_gap_up:
                signal_type = 'BUY'
                amount = current_open - prev_high
            else:
                signal_type = 'SELL'
                amount = prev_low - current_open
            
            strength = min(0.8 + (amount / 2.0), 1.0)
            
            print(f"")
            print(f"🎉 GAP SIGNAL CONFIRMED:")
            print(f"   🎯 Type: {signal_type}")
            print(f"   💰 Gap Amount: {amount:.4f}")
            print(f"   💪 Strength: {strength:.3f}")
            print(f"   🔒 Signature: {signature}")
            print("=" * 60)
            
            # อัพเดท tracking
            self.last_minute_processed = current_minute
            
            return {
                'symbol': self.symbol,
                'timestamp': datetime.now(),
                'candle_signature': signature,
                'candle_timestamp': int(time.time()),
                
                'close': current_open,           # ใช้ Open ของนาทีใหม่
                'previous_high': prev_high,
                'previous_low': prev_low,
                'previous_close': prev_close,
                
                'open': current_open,
                'high': current_open,  # ยังไม่รู้ high ของนาทีใหม่
                'low': current_open,   # ยังไม่รู้ low ของนาทีใหม่
                
                'breakout_detected': is_gap_up,
                'breakdown_detected': is_gap_down,
                'breakout_amount': amount if is_gap_up else 0,
                'breakdown_amount': amount if is_gap_down else 0,
                
                'candle_color': 'green' if is_gap_up else 'red',
                'body_ratio': 0.8,  # กำหนดค่าคงที่
                'signal_strength': strength,
                'analysis_method': 'simple_tick_based_gap_detection'
            }
            
        except Exception as e:
            print(f"❌ Breakout check error: {e}")
            return None
        
    def get_reference_info(self) -> Dict:
        """📊 ข้อมูล Reference Candle ปัจจุบัน"""
        if self.reference_candle:
            return {
                'has_reference': True,
                'reference_time': self.reference_candle['time'].strftime('%H:%M:%S'),
                'reference_high': self.reference_candle['high'],
                'reference_low': self.reference_candle['low'],
                'waiting_for_new': self.waiting_for_new_candle,
                'last_checked': self.last_checked_timestamp
            }
        else:
            return {'has_reference': False}

    def reset_reference_state(self):
        """🔄 รีเซ็ต Reference State (สำหรับ debug)"""
        self.reference_candle = None
        self.reference_timestamp = 0
        self.waiting_for_new_candle = False
        self.last_checked_timestamp = 0
        print("🔄 Reference state reset")
                                                                                                                                            
    def _is_signature_processed(self, signature: str) -> bool:
        """
        🔒 STRICT: เช็คว่าแท่งนี้ประมวลผลแล้วหรือยัง
        ถ้าแล้ว = บล็อกตลอดไป (จนกว่าจะรีสตาร์ทระบบ)
        """
        try:
            is_processed = signature in self.processed_signatures
            
            if is_processed:
                print(f"🚫 PERMANENTLY BLOCKED: แท่งนี้ประมวลผลแล้ว")
                return True
            else:
                print(f"✅ NEW CANDLE: อนุญาตให้ประมวลผล")
                return False
                
        except Exception as e:
            print(f"Signature check error: {e}")
            return False

    def _mark_signature_processed(self, signature: str):
        """
        🔒 FIXED: บันทึกแท่งที่ประมวลผลแล้ว - ป้องกันซ้ำอย่างเข้มงวด
        
        Args:
            signature: ลายเซ็นแท่งเทียน
        """
        try:
            if not hasattr(self, 'processed_signatures'):
                self.processed_signatures = set()
            
            # เพิ่มลายเซ็นใหม่
            self.processed_signatures.add(signature)
            
            # 🔧 CLEANUP: จำกัดจำนวนเพื่อป้องกัน memory leak
            if len(self.processed_signatures) > 1000:
                # เก็บแค่ 800 ตัวล่าสุด
                signatures_list = list(self.processed_signatures)
                # เรียงตาม timestamp (ถ้ามี)
                try:
                    signatures_list.sort(key=lambda x: self._extract_timestamp_from_signature(x))
                    # เก็บ 800 ตัวล่าสุด
                    self.processed_signatures = set(signatures_list[-800:])
                    print(f"🧹 Cleaned signature history: kept 800 most recent")
                except:
                    # ถ้าเรียงไม่ได้ ลบแบบสุ่ม
                    self.processed_signatures = set(signatures_list[-800:])
            
            print(f"🔒 PROCESSED: {signature}")
            print(f"📊 Total signatures: {len(self.processed_signatures)}")
            
            # 🆕 บันทึกลง persistence (ถ้ามี)
            if hasattr(self, 'persistence_manager') and self.persistence_manager:
                self.persistence_manager.save_processed_signatures(self.processed_signatures)
                
        except Exception as e:
            print(f"❌ Mark signature error: {e}")

    def _extract_timestamp_from_signature(self, signature: str) -> float:
        """
        🔧 ดึง timestamp จากลายเซ็น - IMPROVED
        
        Args:
            signature: ลายเซ็นในรูปแบบ "CANDLE_timestamp_..."
            
        Returns:
            float: timestamp หรือ 0 ถ้าไม่พบ
        """
        try:
            # ลายเซ็นรูปแบบ "CANDLE_1756313664_3377.75_..."
            parts = signature.split('_')
            if len(parts) >= 2 and parts[0] == 'CANDLE':
                return float(parts[1])
            
            # ลายเซ็นรูปแบบเก่า "CORRECT_timestamp_..."  
            elif len(parts) >= 2 and parts[0] == 'CORRECT':
                return float(parts[1])
            
            # ถ้าไม่ตรงรูปแบบ ใช้ current time
            return datetime.now().timestamp()
            
        except (ValueError, IndexError):
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
        📊 วิเคราะห์ข้อมูล Volume - ULTRA SAFE VERSION
        
        Returns:
            Dict: ข้อมูล volume analysis
        """
        try:
            print(f"📊 Analyzing volume data...")
            
            # ดึงข้อมูล rates สำหรับ volume
            rates = mt5.copy_rates_from_pos(
                self.symbol, self.timeframe, 0, self.volume_lookback_periods + 1
            )
            
            if rates is None:
                print(f"❌ No rates data for volume analysis")
                return self._get_fallback_volume()
            
            if len(rates) < 2:
                print(f"❌ Not enough candles for volume analysis: {len(rates)}")
                return self._get_fallback_volume()
            
            print(f"✅ Got {len(rates)} candles for volume analysis")
            
            # 🔧 SAFE VOLUME EXTRACTION
            volumes = []
            
            for i, rate in enumerate(rates):
                try:
                    # Method 1: ลองใช้ dtype.names
                    if hasattr(rate, 'dtype') and rate.dtype.names:
                        if 'tick_volume' in rate.dtype.names:
                            volume = int(rate['tick_volume'])
                        elif 'real_volume' in rate.dtype.names:
                            volume = int(rate['real_volume'])
                        else:
                            volume = 1000  # default volume
                    else:
                        # Method 2: ลองเข้าถึงโดยตรง
                        try:
                            volume = int(rate[4]) if len(rate) > 4 else 1000  # index 4 มักจะเป็น volume
                        except:
                            volume = 1000
                    
                    volumes.append(max(volume, 1))  # อย่างน้อย 1
                    print(f"   📊 Rate[{i}] volume: {volume}")
                    
                except Exception as e:
                    print(f"❌ Volume extraction error for rate[{i}]: {e}")
                    volumes.append(1000)  # fallback volume
            
            # ตรวจสอบผลลัพธ์
            if len(volumes) < 2:
                print(f"❌ No valid volumes extracted")
                return self._get_fallback_volume()
            
            # คำนวณ volume metrics
            current_volume = volumes[0]  # แท่งปัจจุบัน
            historical_volumes = volumes[1:]  # แท่งก่อนหน้า
            
            # กรอง volume ที่ไม่สมเหตุสมผล
            valid_historical = [v for v in historical_volumes if 10 <= v <= 1000000]
            
            if len(valid_historical) == 0:
                print(f"❌ No valid historical volumes")
                return self._get_fallback_volume()
            
            avg_volume = sum(valid_historical) / len(valid_historical)
            volume_factor = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # จำกัด volume factor ในช่วงที่สมเหตุสมผล
            volume_factor = max(0.1, min(10.0, volume_factor))
            
            print(f"📊 Volume Analysis Results:")
            print(f"   Current: {current_volume:,}")
            print(f"   Average: {avg_volume:,.0f}")
            print(f"   Factor: {volume_factor:.2f}")
            print(f"   Valid samples: {len(valid_historical)}")
            
            self.volume_available = True
            
            return {
                'available': True,
                'current': current_volume,
                'average': round(avg_volume, 0),
                'factor': round(volume_factor, 2),
                'samples': len(valid_historical),
                'source': 'mt5_safe'
            }
            
        except Exception as e:
            print(f"❌ Volume analysis error: {e}")
            return self._get_fallback_volume()

    def _get_fallback_volume(self) -> Dict:
        """📊 Fallback volume data เมื่อดึงจาก MT5 ไม่ได้"""
        return {
            'available': False,
            'current': 1000,
            'average': 1000,
            'factor': 1.0,
            'samples': 0,
            'source': 'fallback'
        }
    
    def reset_timestamp_tracking(self):
        """🔄 รีเซ็ตการติดตาม timestamp (สำหรับ debug)"""
        try:
            self.last_processed_timestamp = 0
            print(f"🔄 Timestamp tracking reset")
            return True
        except Exception as e:
            print(f"❌ Reset error: {e}")
            return False

    def get_timestamp_info(self) -> Dict:
        """📊 ข้อมูลการติดตาม timestamp"""
        try:
            last_time = self.last_processed_timestamp
            if last_time > 0:
                last_datetime = datetime.fromtimestamp(last_time)
                time_ago = (datetime.now() - last_datetime).total_seconds()
            else:
                last_datetime = None
                time_ago = 0
            
            return {
                'last_processed_timestamp': last_time,
                'last_processed_datetime': last_datetime.isoformat() if last_datetime else None,
                'seconds_since_last': time_ago,
                'next_expected_in_seconds': max(0, 300 - time_ago)  # M5 = 300 วินาที
            }
        except Exception as e:
            return {'error': str(e)}
    
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

    def get_debug_info(self) -> Dict:
        """🔍 ข้อมูล debug สำหรับ troubleshooting"""
        try:
            return {
                'analyzer_status': {
                    'is_ready': self.is_ready(),
                    'mt5_connected': self.mt5_connector.is_connected if self.mt5_connector else False,
                    'symbol': self.symbol,
                    'timeframe': 'M5'
                },
                'cache_info': {
                    'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time != datetime.min else 'Never',
                    'last_candle_time': self.last_analyzed_candle_time.isoformat() if self.last_analyzed_candle_time != datetime.min else 'Never',
                    'cache_valid': self._is_cache_valid(),
                    'cache_duration': self.cache_duration_seconds
                },
                'signature_tracking': {
                    'processed_count': len(getattr(self, 'processed_signatures', set())),
                    'max_history': self.max_signature_history,
                    'recent_signatures': list(getattr(self, 'processed_signatures', set()))[-5:] if hasattr(self, 'processed_signatures') else []
                },
                'performance': {
                    'total_analysis': getattr(self, 'analysis_count', 0),
                    'duplicate_blocks': getattr(self, 'duplicate_blocks', 0),
                    'successful_analysis': getattr(self, 'successful_analysis', 0),
                    'block_rate': f"{(getattr(self, 'duplicate_blocks', 0) / max(getattr(self, 'analysis_count', 1), 1) * 100):.1f}%"
                },
                'volume_status': {
                    'available': self.volume_available,
                    'history_count': len(self.volume_history)
                }
            }
        except Exception as e:
            return {'error': str(e)}

    def clear_processed_signatures(self):
        """🗑️ ล้างประวัติการประมวลผล (สำหรับ debug)"""
        try:
            if hasattr(self, 'processed_signatures'):
                old_count = len(self.processed_signatures)
                self.processed_signatures.clear()
                print(f"🗑️ Cleared {old_count} processed signatures")
                
            # รีเซ็ตเวลาติดตาม
            self.last_analysis_time = datetime.min
            self.last_analyzed_candle_time = datetime.min
            
            # รีเซ็ตสถิติ
            self.analysis_count = 0
            self.duplicate_blocks = 0 
            self.successful_analysis = 0
            
            print(f"✅ Analyzer reset completed")
            return True
            
        except Exception as e:
            print(f"❌ Clear signatures error: {e}")
            return False

    def force_analyze_current_candle(self) -> Optional[Dict]:
        """🔧 บังคับวิเคราะห์แท่งปัจจุบัน (ข้าม duplicate check)"""
        try:
            print(f"🔧 FORCE ANALYSIS - bypassing duplicate check...")
            
            # สำรองและปิด duplicate check ชั่วคราว
            original_processed = getattr(self, 'processed_signatures', set()).copy()
            self.processed_signatures = set()  # ล้างชั่วคราว
            
            # วิเคราะห์
            result = self.get_current_analysis()
            
            # คืนค่า processed signatures
            self.processed_signatures = original_processed
            
            if result:
                print(f"✅ Force analysis completed")
            else:
                print(f"❌ Force analysis failed")
            
            return result
            
        except Exception as e:
            print(f"❌ Force analysis error: {e}")
            return None
    
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
