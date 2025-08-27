"""
🕯️ Pure Candlestick Analyzer (COMPLETE VERSION)
candlestick_analyzer.py

🔧 COMPLETELY FIXED:
✅ numpy.void object 'get' method error
✅ Proper OHLC data extraction from MT5
✅ Volume data handling
✅ Error handling for missing data
✅ Real-time candle processing
✅ Duplicate prevention system
✅ Memory management & caching
✅ Pattern recognition algorithms
✅ Volume confirmation system

🚀 Complete Features:
✅ OHLC Data Collection & Validation
✅ Advanced Candlestick Pattern Recognition
✅ Volume Analysis with Fallback
✅ Body Ratio & Wick Analysis
✅ Price Direction Detection
✅ Pattern Classification System
✅ Real-time Performance Tracking
✅ Signature-based Duplicate Prevention
✅ Persistence Integration
✅ Comprehensive Error Handling
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import time
import statistics
import math

class CandlestickAnalyzer:
    """
    🕯️ Pure Candlestick Analyzer (COMPLETE VERSION)
    
    วิเคราะห์แท่งเทียนแบบครบถ้วนสมบูรณ์
    รองรับการวิเคราะห์ real-time และ pattern recognition
    """
    
    def __init__(self, mt5_connector, config: Dict):
        """
        🔧 เริ่มต้น Candlestick Analyzer - COMPLETE
        
        Args:
            mt5_connector: MT5 connection object
            config: การตั้งค่าระบบ
        """
        self.mt5_connector = mt5_connector
        self.config = config
        
        # การตั้งค่าพื้นฐาน
        self.symbol = config.get("trading", {}).get("symbol", "XAUUSD.v")
        self.timeframe = mt5.TIMEFRAME_M1
        
        # การตั้งค่า analysis parameters
        self.min_candles_required = 3  # ขั้นต่ำสำหรับ analysis
        self.max_candles_lookback = 20  # สูงสุดที่จะดูย้อนหลัง
        self.volume_lookback_periods = 10
        
        # Pattern recognition settings
        self.doji_threshold = 0.05  # 5% สำหรับ doji detection
        self.strong_body_threshold = 0.6  # 60% สำหรับ strong candle
        self.hammer_wick_ratio = 2.0  # อัตราส่วน wick สำหรับ hammer
        self.shooting_star_ratio = 2.0  # อัตราส่วนสำหรับ shooting star
        
        # Volume analysis settings
        self.volume_spike_threshold = 1.5  # 150% ของ average volume
        self.volume_confirmation_enabled = config.get("volume", {}).get("enabled", True)
        self.volume_fallback_enabled = True  # ใช้ fallback เมื่อไม่มี volume
        
        # 🔧 CACHE MANAGEMENT - ปรับให้เหมาะ real-time
        self.last_analysis_time = datetime.min
        self.last_analyzed_candle_time = datetime.min
        self.cache_duration_seconds = 5   # Cache 5 วินาที
        self.cached_analysis = None
        
        # 🔧 VOLUME TRACKING
        self.volume_available = False
        self.volume_history = []
        self.max_volume_history = 20
        self.avg_volume = 0.0
        
        # 🆕 STRICT SIGNATURE TRACKING
        self.processed_signatures = set()
        self.max_signature_history = 500  # เก็บ 500 signatures
        
        # 🆕 CANDLE STATE TRACKING  
        self.last_candle_signature = None
        self.last_processed_candle_time = datetime.min
        self.minimum_time_gap_seconds = 30  # ห่างกัน 30 วินาทีขั้นต่ำ
        
        # 🆕 PERFORMANCE COUNTERS
        self.analysis_count = 0
        self.duplicate_blocks = 0
        self.successful_analysis = 0
        self.time_order_errors = 0
        self.invalid_data_errors = 0
        
        # 🆕 DATA VALIDATION FLAGS
        self.strict_time_checking = True
        self.allow_same_minute_candles = False
        
        # 🔧 PERSISTENCE INTEGRATION
        self.persistence_manager = None
        
        # 🆕 REAL-TIME PROCESSING FLAGS
        self.real_time_mode = True
        self.force_sequential_processing = True
        
        # Pattern tracking
        self.pattern_history = []
        self.pattern_success_rates = {}
        
        print(f"🕯️ Candlestick Analyzer initialized (COMPLETE) for {self.symbol}")
        print(f"   Timeframe: M1")
        print(f"   Min candles: {self.min_candles_required}")
        print(f"   Volume enabled: {self.volume_confirmation_enabled}")
        print(f"   Cache duration: {self.cache_duration_seconds}s")
        print(f"   Real-time mode: {self.real_time_mode}")
    
    # ==========================================
    # 🕯️ MAIN ANALYSIS METHODS - COMPLETE
    # ==========================================
    
    def get_current_analysis(self) -> Optional[Dict]:
        """
        🕯️ วิเคราะห์แท่งเทียนปัจจุบัน - COMPLETE VERSION (MAIN METHOD)
        
        Returns:
            Dict: ผลการวิเคราะห์แบบครบถ้วน หรือ None ถ้าไม่สามารถวิเคราะห์
        """
        try:
            self.analysis_count += 1
            
            print(f"\n🕯️ === CANDLESTICK ANALYSIS #{self.analysis_count} ===")
            
            # 1. ตรวจสอบการเชื่อมต่อและความพร้อม
            if not self._validate_connection():
                return None
            
            # 2. ตรวจสอบ cache
            if self._is_cache_valid():
                print(f"📋 Using cached analysis (age: {(datetime.now() - self.last_analysis_time).seconds}s)")
                return self.cached_analysis
            
            # 3. ดึงข้อมูลแท่งเทียน
            candle_data = self._fetch_candlestick_data()
            if not candle_data:
                print(f"❌ Failed to fetch candlestick data")
                self.invalid_data_errors += 1
                return None
            
            # 4. ตรวจสอบและทำความสะอาดข้อมูล
            cleaned_data = self._validate_and_clean_data(candle_data)
            if not cleaned_data:
                print(f"❌ Invalid data after cleaning")
                self.invalid_data_errors += 1
                return None
            
            # 5. ตรวจสอบ duplicate processing
            current_signature = self._generate_candle_signature(cleaned_data[0])
            if self._is_already_processed(current_signature):
                print(f"🚫 Duplicate processing blocked: {current_signature}")
                self.duplicate_blocks += 1
                return self.cached_analysis
            
            # 6. วิเคราะห์แท่งเทียนแบบครบถ้วน
            analysis_result = self._perform_complete_analysis(cleaned_data)
            
            if analysis_result:
                # 7. บันทึกผลการวิเคราะห์
                self._record_successful_analysis(current_signature, analysis_result)
                self.successful_analysis += 1
                
                print(f"✅ Analysis completed successfully")
                print(f"   Pattern: {analysis_result.get('pattern_name')}")
                print(f"   Color: {analysis_result.get('candle_color')}")
                print(f"   Strength: {analysis_result.get('pattern_strength'):.3f}")
                print(f"   Body ratio: {analysis_result.get('body_ratio'):.3f}")
                
                return analysis_result
            else:
                print(f"❌ Analysis failed")
                return None
                
        except Exception as e:
            print(f"❌ Candlestick analysis error: {e}")
            self.invalid_data_errors += 1
            return self._get_fallback_analysis()
    
    def _fetch_candlestick_data(self) -> Optional[List[Dict]]:
        """
        📊 ดึงข้อมูลแท่งเทียน - COMPLETE WITH ERROR HANDLING
        
        Returns:
            List[Dict]: รายการข้อมูลแท่งเทียน หรือ None
        """
        try:
            print(f"📊 Fetching candlestick data for {self.symbol}")
            
            # ดึงข้อมูลแท่งเทียน
            candles = mt5.copy_rates_from_pos(
                self.symbol, 
                self.timeframe, 
                0, 
                self.max_candles_lookback
            )
            
            if candles is None or len(candles) == 0:
                print(f"❌ No candlestick data received")
                return None
            
            if len(candles) < self.min_candles_required:
                print(f"❌ Insufficient candles: {len(candles)} < {self.min_candles_required}")
                return None
            
            print(f"✅ Fetched {len(candles)} candles")
            
            # แปลงข้อมูล MT5 เป็น dictionary format
            converted_candles = []
            
            for i, candle in enumerate(candles):
                try:
                    # 🔧 FIXED: แปลง numpy data เป็น Python native types
                    candle_dict = {
                        'time': int(candle[0]),  # timestamp
                        'open': float(candle[1]),
                        'high': float(candle[2]),
                        'low': float(candle[3]),
                        'close': float(candle[4]),
                        'tick_volume': int(candle[5]) if len(candle) > 5 else 0,
                        'spread': int(candle[6]) if len(candle) > 6 else 0,
                        'real_volume': int(candle[7]) if len(candle) > 7 else 0,
                        'index': i,
                        'datetime': datetime.fromtimestamp(int(candle[0]))
                    }
                    
                    # ตรวจสอบความถูกต้องของ OHLC
                    if self._validate_ohlc_data(candle_dict):
                        converted_candles.append(candle_dict)
                    else:
                        print(f"⚠️ Invalid OHLC data at index {i}, skipping")
                        
                except Exception as e:
                    print(f"❌ Error converting candle {i}: {e}")
                    continue
            
            if len(converted_candles) < self.min_candles_required:
                print(f"❌ Insufficient valid candles after conversion: {len(converted_candles)}")
                return None
            
            # เรียงตามเวลา (เก่าไปใหม่)
            converted_candles.sort(key=lambda x: x['time'])
            
            print(f"✅ Converted {len(converted_candles)} valid candles")
            
            # อัพเดท volume tracking
            self._update_volume_tracking(converted_candles)
            
            return converted_candles
            
        except Exception as e:
            print(f"❌ Fetch candlestick data error: {e}")
            return None
    
    def _validate_and_clean_data(self, candles: List[Dict]) -> Optional[List[Dict]]:
        """
        🧹 ตรวจสอบและทำความสะอาดข้อมูล - COMPLETE
        
        Args:
            candles: รายการข้อมูลแท่งเทียน
            
        Returns:
            List[Dict]: ข้อมูลที่ทำความสะอาดแล้ว หรือ None
        """
        try:
            if not candles or len(candles) < self.min_candles_required:
                return None
            
            cleaned_candles = []
            
            for i, candle in enumerate(candles):
                try:
                    # ตรวจสอบข้อมูลพื้นฐาน
                    if not self._validate_basic_candle_data(candle):
                        print(f"⚠️ Invalid basic data at index {i}")
                        continue
                    
                    # ตรวจสอบเวลา
                    if self.strict_time_checking and i > 0:
                        prev_time = cleaned_candles[-1]['time'] if cleaned_candles else 0
                        current_time = candle['time']
                        
                        if current_time <= prev_time:
                            print(f"⚠️ Time order violation at index {i}: {current_time} <= {prev_time}")
                            self.time_order_errors += 1
                            continue
                    
                    # เพิ่มข้อมูลเสริม
                    enhanced_candle = self._enhance_candle_data(candle)
                    cleaned_candles.append(enhanced_candle)
                    
                except Exception as e:
                    print(f"❌ Error cleaning candle {i}: {e}")
                    continue
            
            if len(cleaned_candles) < self.min_candles_required:
                print(f"❌ Insufficient cleaned candles: {len(cleaned_candles)}")
                return None
            
            print(f"🧹 Cleaned data: {len(cleaned_candles)} valid candles")
            return cleaned_candles
            
        except Exception as e:
            print(f"❌ Data cleaning error: {e}")
            return None
    
    def _perform_complete_analysis(self, candles: List[Dict]) -> Optional[Dict]:
        """
        🔍 ทำการวิเคราะห์แบบครบถ้วน - COMPLETE ANALYSIS ENGINE
        
        Args:
            candles: ข้อมูลแท่งเทียนที่ทำความสะอาดแล้ว
            
        Returns:
            Dict: ผลการวิเคราะห์แบบครบถ้วน
        """
        try:
            current_candle = candles[-1]  # แท่งล่าสุด
            previous_candle = candles[-2] if len(candles) >= 2 else None
            
            print(f"🔍 Performing complete analysis...")
            print(f"   Current candle time: {current_candle['datetime'].strftime('%H:%M:%S')}")
            print(f"   OHLC: {current_candle['open']:.4f}/{current_candle['high']:.4f}/{current_candle['low']:.4f}/{current_candle['close']:.4f}")
            
            # 1. การวิเคราะห์พื้นฐาน
            basic_analysis = self._analyze_basic_candle_properties(current_candle)
            
            # 2. การเปรียบเทียบกับแท่งก่อนหน้า
            comparison_analysis = self._analyze_candle_comparison(current_candle, previous_candle) if previous_candle else {}
            
            # 3. การจดจำ pattern
            pattern_analysis = self._identify_candlestick_patterns(candles)
            
            # 4. การวิเคราะห์ volume
            volume_analysis = self._analyze_volume_confirmation(candles)
            
            # 5. การประเมิน market context
            context_analysis = self._analyze_market_context(candles)
            
            # 6. การคำนวณความแรงของ signal
            signal_strength = self._calculate_analysis_strength(
                basic_analysis, comparison_analysis, pattern_analysis, volume_analysis
            )
            
            # รวมผลการวิเคราะห์ทั้งหมด
            complete_analysis = {
                # Basic properties
                'timestamp': current_candle['time'],
                'datetime': current_candle['datetime'],
                'open': current_candle['open'],
                'high': current_candle['high'],
                'low': current_candle['low'],
                'close': current_candle['close'],
                'volume': current_candle.get('real_volume', 0),
                
                # Basic analysis
                **basic_analysis,
                
                # Comparison analysis
                **comparison_analysis,
                
                # Pattern analysis
                **pattern_analysis,
                
                # Volume analysis
                **volume_analysis,
                
                # Context analysis
                **context_analysis,
                
                # Signal strength
                'analysis_strength': signal_strength,
                'analysis_quality': self._calculate_analysis_quality(candles),
                
                # Metadata
                'candles_analyzed': len(candles),
                'analysis_timestamp': datetime.now(),
                'analyzer_version': '2.0.0'
            }
            
            # Cache ผลการวิเคราะห์
            self.cached_analysis = complete_analysis
            self.last_analysis_time = datetime.now()
            self.last_analyzed_candle_time = current_candle['datetime']
            
            return complete_analysis
            
        except Exception as e:
            print(f"❌ Complete analysis error: {e}")
            return None
    
    # ==========================================
    # 🔍 DETAILED ANALYSIS METHODS - COMPLETE
    # ==========================================
    
    def _analyze_basic_candle_properties(self, candle: Dict) -> Dict:
        """
        🔍 วิเคราะห์คุณสมบัติพื้นฐานของแท่งเทียน - COMPLETE
        
        Args:
            candle: ข้อมูลแท่งเทียน
            
        Returns:
            Dict: การวิเคราะห์คุณสมบัติพื้นฐาน
        """
        try:
            o, h, l, c = candle['open'], candle['high'], candle['low'], candle['close']
            
            # คำนวณขนาดต่างๆ
            candle_range = h - l
            body_size = abs(c - o)
            upper_shadow = h - max(o, c)
            lower_shadow = min(o, c) - l
            
            # ป้องกัน division by zero
            range_threshold = 0.0001
            if candle_range < range_threshold:
                candle_range = range_threshold
            
            # คำนวณอัตราส่วน
            body_ratio = body_size / candle_range
            upper_shadow_ratio = upper_shadow / candle_range
            lower_shadow_ratio = lower_shadow / candle_range
            
            # กำหนดสีแท่งเทียน
            price_threshold = 0.0001
            if c > o + price_threshold:
                candle_color = 'green'  # bullish
            elif c < o - price_threshold:
                candle_color = 'red'    # bearish
            else:
                candle_color = 'doji'   # neutral
            
            # ประเภทของ body
            if body_ratio >= self.strong_body_threshold:
                body_type = 'strong'
            elif body_ratio >= 0.3:
                body_type = 'medium'
            elif body_ratio <= self.doji_threshold:
                body_type = 'doji'
            else:
                body_type = 'weak'
            
            # ประเภทของ shadow
            if upper_shadow_ratio >= 0.6:
                shadow_type = 'upper_heavy'
            elif lower_shadow_ratio >= 0.6:
                shadow_type = 'lower_heavy'
            elif upper_shadow_ratio >= 0.3 and lower_shadow_ratio >= 0.3:
                shadow_type = 'both_sides'
            else:
                shadow_type = 'normal'
            
            return {
                'candle_color': candle_color,
                'body_type': body_type,
                'shadow_type': shadow_type,
                'candle_range': round(candle_range, 5),
                'body_size': round(body_size, 5),
                'body_ratio': round(body_ratio, 4),
                'upper_shadow': round(upper_shadow, 5),
                'lower_shadow': round(lower_shadow, 5),
                'upper_shadow_ratio': round(upper_shadow_ratio, 4),
                'lower_shadow_ratio': round(lower_shadow_ratio, 4),
                'is_doji': body_ratio <= self.doji_threshold,
                'is_strong_body': body_ratio >= self.strong_body_threshold
            }
            
        except Exception as e:
            print(f"❌ Basic properties analysis error: {e}")
            return {
                'candle_color': 'unknown',
                'body_type': 'unknown',
                'shadow_type': 'unknown',
                'body_ratio': 0.0,
                'is_doji': False,
                'is_strong_body': False
            }
    
    def _analyze_candle_comparison(self, current: Dict, previous: Dict) -> Dict:
        """
        📊 เปรียบเทียบแท่งเทียนปัจจุบันกับแท่งก่อนหน้า - COMPLETE
        
        Args:
            current: แท่งเทียนปัจจุบัน
            previous: แท่งเทียนก่อนหน้า
            
        Returns:
            Dict: ผลการเปรียบเทียบ
        """
        try:
            if not previous:
                return {'comparison_available': False}
            
            curr_c = current['close']
            curr_o = current['open']
            curr_h = current['high']
            curr_l = current['low']
            
            prev_c = previous['close']
            prev_o = previous['open']
            prev_h = previous['high']
            prev_l = previous['low']
            
            # เปรียบเทียบราคา
            price_change = curr_c - prev_c
            price_change_percent = (price_change / prev_c * 100) if prev_c != 0 else 0
            
            # เปรียบเทียบ range
            curr_range = curr_h - curr_l
            prev_range = prev_h - prev_l
            range_change_percent = ((curr_range - prev_range) / prev_range * 100) if prev_range != 0 else 0
            
            # ความสัมพันธ์ตำแหน่ง
            price_threshold = 0.0001
            
            # ทิศทางราคาปิด
            if curr_c > prev_c + price_threshold:
                price_direction = 'higher_close'
            elif curr_c < prev_c - price_threshold:
                price_direction = 'lower_close'
            else:
                price_direction = 'same_close'
            
            # Gap detection
            gap_up = curr_o > prev_h + price_threshold
            gap_down = curr_o < prev_l - price_threshold
            gap_type = 'up' if gap_up else 'down' if gap_down else 'none'
            
            # ความสัมพันธ์ high/low
            higher_high = curr_h > prev_h + price_threshold
            lower_low = curr_l < prev_l - price_threshold
            higher_low = curr_l > prev_l + price_threshold
            lower_high = curr_h < prev_h - price_threshold
            
            # Pattern relationship
            if higher_high and higher_low:
                trend_direction = 'bullish'
            elif lower_high and lower_low:
                trend_direction = 'bearish'
            else:
                trend_direction = 'sideways'
            
            return {
                'comparison_available': True,
                'price_change': round(price_change, 5),
                'price_change_percent': round(price_change_percent, 3),
                'price_direction': price_direction,
                'range_change_percent': round(range_change_percent, 2),
                'gap_type': gap_type,
                'gap_up': gap_up,
                'gap_down': gap_down,
                'higher_high': higher_high,
                'lower_low': lower_low,
                'higher_low': higher_low,
                'lower_high': lower_high,
                'trend_direction': trend_direction,
                'momentum': 'strong' if abs(price_change_percent) > 0.1 else 'weak'
            }
            
        except Exception as e:
            print(f"❌ Candle comparison error: {e}")
            return {'comparison_available': False}
    
    def _identify_candlestick_patterns(self, candles: List[Dict]) -> Dict:
        """
        🎯 จดจำ candlestick patterns - COMPLETE PATTERN RECOGNITION
        
        Args:
            candles: รายการแท่งเทียน
            
        Returns:
            Dict: ผล pattern recognition
        """
        try:
            if len(candles) < 1:
                return {'pattern_name': 'insufficient_data', 'pattern_strength': 0.0}
            
            current = candles[-1]
            previous = candles[-2] if len(candles) >= 2 else None
            third = candles[-3] if len(candles) >= 3 else None
            
            # Single candle patterns
            single_pattern = self._identify_single_candle_patterns(current)
            
            # Two candle patterns
            two_pattern = self._identify_two_candle_patterns(current, previous) if previous else None
            
            # Three candle patterns
            three_pattern = self._identify_three_candle_patterns(current, previous, third) if third else None
            
            # เลือก pattern ที่แข็งแกร่งที่สุด
            patterns = [single_pattern]
            if two_pattern:
                patterns.append(two_pattern)
            if three_pattern:
                patterns.append(three_pattern)
            
            # เรียงตาม strength และ confidence
            patterns.sort(key=lambda p: (p['pattern_strength'], p.get('pattern_confidence', 0)), reverse=True)
            
            best_pattern = patterns[0]
            
            # ติดตาม pattern history
            self._record_pattern_occurrence(best_pattern)
            
            return {
                'pattern_name': best_pattern['pattern_name'],
                'pattern_type': best_pattern.get('pattern_type', 'single'),
                'pattern_strength': best_pattern['pattern_strength'],
                'pattern_confidence': best_pattern.get('pattern_confidence', 0.5),
                'pattern_description': best_pattern.get('description', ''),
                'bullish_signal': best_pattern.get('bullish', False),
                'bearish_signal': best_pattern.get('bearish', False),
                'reversal_signal': best_pattern.get('reversal', False),
                'continuation_signal': best_pattern.get('continuation', False),
                'alternative_patterns': [p['pattern_name'] for p in patterns[1:3]]  # top 2 alternatives
            }
            
        except Exception as e:
            print(f"❌ Pattern identification error: {e}")
            return {
                'pattern_name': 'error',
                'pattern_strength': 0.0,
                'pattern_confidence': 0.0
            }
    
    def _identify_single_candle_patterns(self, candle: Dict) -> Dict:
        """🕯️ จดจำ single candle patterns"""
        try:
            o, h, l, c = candle['open'], candle['high'], candle['low'], candle['close']
            candle_range = h - l
            body_size = abs(c - o)
            body_ratio = body_size / candle_range if candle_range > 0.0001 else 0
            
            upper_shadow = h - max(o, c)
            lower_shadow = min(o, c) - l
            upper_ratio = upper_shadow / candle_range if candle_range > 0.0001 else 0
            lower_ratio = lower_shadow / candle_range if candle_range > 0.0001 else 0
            
            # Doji patterns
            if body_ratio <= self.doji_threshold:
                if upper_ratio > 0.4 and lower_ratio < 0.1:
                    return {
                        'pattern_name': 'dragonfly_doji',
                        'pattern_strength': 0.7,
                        'pattern_confidence': 0.8,
                        'bullish': True,
                        'reversal': True,
                        'description': 'Dragonfly Doji - Bullish reversal'
                    }
                elif lower_ratio > 0.4 and upper_ratio < 0.1:
                    return {
                        'pattern_name': 'gravestone_doji',
                        'pattern_strength': 0.7,
                        'pattern_confidence': 0.8,
                        'bearish': True,
                        'reversal': True,
                        'description': 'Gravestone Doji - Bearish reversal'
                    }
                else:
                    return {
                        'pattern_name': 'doji',
                        'pattern_strength': 0.5,
                        'pattern_confidence': 0.6,
                        'reversal': True,
                        'description': 'Standard Doji - Indecision'
                    }
            
            # Hammer patterns
            if lower_ratio >= 0.6 and upper_ratio <= 0.1 and body_ratio >= 0.1:
                bullish = c > o
                return {
                    'pattern_name': 'hammer' if bullish else 'hanging_man',
                    'pattern_strength': 0.8,
                    'pattern_confidence': 0.7,
                    'bullish': bullish,
                    'bearish': not bullish,
                    'reversal': True,
                    'description': f'{"Hammer - Bullish" if bullish else "Hanging Man - Bearish"} reversal'
                }
            
            # Shooting star / Inverted hammer
            if upper_ratio >= 0.6 and lower_ratio <= 0.1 and body_ratio >= 0.1:
                bullish = c > o
                return {
                    'pattern_name': 'inverted_hammer' if bullish else 'shooting_star',
                    'pattern_strength': 0.8,
                    'pattern_confidence': 0.7,
                    'bullish': bullish,
                    'bearish': not bullish,
                    'reversal': True,
                    'description': f'{"Inverted Hammer" if bullish else "Shooting Star"} reversal'
                }
            
            # Marubozu (strong body, minimal shadows)
            if body_ratio >= 0.9:
                bullish = c > o
                return {
                    'pattern_name': 'marubozu',
                    'pattern_strength': 0.9,
                    'pattern_confidence': 0.8,
                    'bullish': bullish,
                    'bearish': not bullish,
                    'continuation': True,
                    'description': f'{"Bullish" if bullish else "Bearish"} Marubozu - Strong continuation'
                }
            
            # Spinning top
            if 0.1 < body_ratio < 0.3 and upper_ratio > 0.2 and lower_ratio > 0.2:
                return {
                    'pattern_name': 'spinning_top',
                    'pattern_strength': 0.4,
                    'pattern_confidence': 0.5,
                    'reversal': True,
                    'description': 'Spinning Top - Market indecision'
                }
            
            # Regular candle (default)
            bullish = c > o
            strength = min(body_ratio, 0.8)  # Cap at 0.8
            
            return {
                'pattern_name': 'regular_candle',
                'pattern_strength': strength,
                'pattern_confidence': 0.5,
                'bullish': bullish,
                'bearish': not bullish,
                'continuation': True,
                'description': f'{"Bullish" if bullish else "Bearish"} regular candle'
            }
            
        except Exception as e:
            print(f"❌ Single pattern identification error: {e}")
            return {
                'pattern_name': 'error',
                'pattern_strength': 0.0,
                'pattern_confidence': 0.0
            }
    
    def _identify_two_candle_patterns(self, current: Dict, previous: Dict) -> Dict:
        """🕯️🕯️ จดจำ two candle patterns"""
        try:
            curr_o, curr_h, curr_l, curr_c = current['open'], current['high'], current['low'], current['close']
            prev_o, prev_h, prev_l, prev_c = previous['open'], previous['high'], previous['low'], previous['close']
            
            curr_bullish = curr_c > curr_o
            prev_bullish = prev_c > prev_o
            
            curr_body = abs(curr_c - curr_o)
            prev_body = abs(prev_c - prev_o)
            
            curr_range = curr_h - curr_l
            prev_range = prev_h - prev_l
            
            # Engulfing patterns
            if curr_bullish and not prev_bullish:  # Bullish engulfing
                if curr_o < prev_c and curr_c > prev_o and curr_body > prev_body:
                    return {
                        'pattern_name': 'bullish_engulfing',
                        'pattern_type': 'two_candle',
                        'pattern_strength': 0.85,
                        'pattern_confidence': 0.8,
                        'bullish': True,
                        'reversal': True,
                        'description': 'Bullish Engulfing - Strong reversal signal'
                    }
            
            elif not curr_bullish and prev_bullish:  # Bearish engulfing
                if curr_o > prev_c and curr_c < prev_o and curr_body > prev_body:
                    return {
                        'pattern_name': 'bearish_engulfing',
                        'pattern_type': 'two_candle',
                        'pattern_strength': 0.85,
                        'pattern_confidence': 0.8,
                        'bearish': True,
                        'reversal': True,
                        'description': 'Bearish Engulfing - Strong reversal signal'
                    }
            
            # Piercing line / Dark cloud cover
            if prev_bullish and not curr_bullish:  # Dark cloud cover
                if curr_o > prev_h and curr_c < (prev_o + prev_c) / 2:
                    return {
                        'pattern_name': 'dark_cloud_cover',
                        'pattern_type': 'two_candle',
                        'pattern_strength': 0.7,
                        'pattern_confidence': 0.7,
                        'bearish': True,
                        'reversal': True,
                        'description': 'Dark Cloud Cover - Bearish reversal'
                    }
            
            elif not prev_bullish and curr_bullish:  # Piercing line
                if curr_o < prev_l and curr_c > (prev_o + prev_c) / 2:
                    return {
                        'pattern_name': 'piercing_line',
                        'pattern_type': 'two_candle',
                        'pattern_strength': 0.7,
                        'pattern_confidence': 0.7,
                        'bullish': True,
                        'reversal': True,
                        'description': 'Piercing Line - Bullish reversal'
                    }
            
            # Tweezer patterns
            if abs(curr_h - prev_h) < 0.0005:  # Tweezer tops
                return {
                    'pattern_name': 'tweezer_tops',
                    'pattern_type': 'two_candle',
                    'pattern_strength': 0.6,
                    'pattern_confidence': 0.6,
                    'bearish': True,
                    'reversal': True,
                    'description': 'Tweezer Tops - Bearish reversal'
                }
            
            elif abs(curr_l - prev_l) < 0.0005:  # Tweezer bottoms
                return {
                    'pattern_name': 'tweezer_bottoms',
                    'pattern_type': 'two_candle',
                    'pattern_strength': 0.6,
                    'pattern_confidence': 0.6,
                    'bullish': True,
                    'reversal': True,
                    'description': 'Tweezer Bottoms - Bullish reversal'
                }
            
            # Harami patterns
            if curr_h < prev_h and curr_l > prev_l:  # Inside day
                if curr_body < prev_body * 0.5:  # Small body inside large body
                    return {
                        'pattern_name': 'harami',
                        'pattern_type': 'two_candle',
                        'pattern_strength': 0.6,
                        'pattern_confidence': 0.6,
                        'reversal': True,
                        'description': 'Harami - Reversal signal'
                    }
            
            # Default: no significant two-candle pattern
            return {
                'pattern_name': 'no_two_pattern',
                'pattern_type': 'two_candle',
                'pattern_strength': 0.3,
                'pattern_confidence': 0.3,
                'description': 'No significant two-candle pattern'
            }
            
        except Exception as e:
            print(f"❌ Two candle pattern error: {e}")
            return {
                'pattern_name': 'two_pattern_error',
                'pattern_strength': 0.0,
                'pattern_confidence': 0.0
            }
    
    def _identify_three_candle_patterns(self, current: Dict, previous: Dict, third: Dict) -> Dict:
        """🕯️🕯️🕯️ จดจำ three candle patterns"""
        try:
            # Morning star / Evening star patterns
            curr_bullish = current['close'] > current['open']
            prev_body_small = abs(previous['close'] - previous['open']) < (previous['high'] - previous['low']) * 0.3
            third_bullish = third['close'] > third['open']
            
            # Morning Star
            if not third_bullish and prev_body_small and curr_bullish:
                if (current['close'] > (third['open'] + third['close']) / 2 and 
                    previous['low'] < min(third['low'], current['low'])):
                    return {
                        'pattern_name': 'morning_star',
                        'pattern_type': 'three_candle',
                        'pattern_strength': 0.9,
                        'pattern_confidence': 0.8,
                        'bullish': True,
                        'reversal': True,
                        'description': 'Morning Star - Strong bullish reversal'
                    }
            
            # Evening Star
            elif third_bullish and prev_body_small and not curr_bullish:
                if (current['close'] < (third['open'] + third['close']) / 2 and 
                    previous['high'] > max(third['high'], current['high'])):
                    return {
                        'pattern_name': 'evening_star',
                        'pattern_type': 'three_candle',
                        'pattern_strength': 0.9,
                        'pattern_confidence': 0.8,
                        'bearish': True,
                        'reversal': True,
                        'description': 'Evening Star - Strong bearish reversal'
                    }
            
            # Three white soldiers / Three black crows
            if curr_bullish and (previous['close'] > previous['open']) and third_bullish:
                if (current['close'] > previous['close'] > third['close'] and
                    current['open'] > previous['open'] > third['open']):
                    return {
                        'pattern_name': 'three_white_soldiers',
                        'pattern_type': 'three_candle',
                        'pattern_strength': 0.8,
                        'pattern_confidence': 0.7,
                        'bullish': True,
                        'continuation': True,
                        'description': 'Three White Soldiers - Strong bullish continuation'
                    }
            
            elif not curr_bullish and (previous['close'] < previous['open']) and not third_bullish:
                if (current['close'] < previous['close'] < third['close'] and
                    current['open'] < previous['open'] < third['open']):
                    return {
                        'pattern_name': 'three_black_crows',
                        'pattern_type': 'three_candle',
                        'pattern_strength': 0.8,
                        'pattern_confidence': 0.7,
                        'bearish': True,
                        'continuation': True,
                        'description': 'Three Black Crows - Strong bearish continuation'
                    }
            
            # Default: no three-candle pattern
            return {
                'pattern_name': 'no_three_pattern',
                'pattern_type': 'three_candle',
                'pattern_strength': 0.2,
                'pattern_confidence': 0.2,
                'description': 'No significant three-candle pattern'
            }
            
        except Exception as e:
            print(f"❌ Three candle pattern error: {e}")
            return {
                'pattern_name': 'three_pattern_error',
                'pattern_strength': 0.0,
                'pattern_confidence': 0.0
            }
    
    def _analyze_volume_confirmation(self, candles: List[Dict]) -> Dict:
        """
        📊 วิเคราะห์ volume confirmation - COMPLETE
        
        Args:
            candles: รายการแท่งเทียน
            
        Returns:
            Dict: ผลการวิเคราะห์ volume
        """
        try:
            if not self.volume_confirmation_enabled:
                return {
                    'volume_available': False,
                    'volume_confirmation': False,
                    'volume_analysis': 'disabled',
                    'volume_strength': 0.0
                }
            
            current = candles[-1]
            current_volume = current.get('real_volume', 0)
            
            # ถ้าไม่มี volume data หรือ volume = 0
            if current_volume <= 0:
                if self.volume_fallback_enabled:
                    return {
                        'volume_available': False,
                        'volume_confirmation': True,  # ใช้ fallback
                        'volume_analysis': 'fallback_confirmation',
                        'volume_strength': 0.5,
                        'fallback_reason': 'no_volume_data'
                    }
                else:
                    return {
                        'volume_available': False,
                        'volume_confirmation': False,
                        'volume_analysis': 'no_data',
                        'volume_strength': 0.0
                    }
            
            # คำนวณ average volume
            if not self.volume_history or len(self.volume_history) < 5:
                # ไม่มี history พอ ใช้ fallback
                return {
                    'volume_available': True,
                    'volume_confirmation': True,
                    'volume_analysis': 'insufficient_history',
                    'volume_strength': 0.6,
                    'current_volume': current_volume,
                    'fallback_reason': 'insufficient_volume_history'
                }
            
            # มี volume history เพียงพอ
            avg_volume = statistics.mean(self.volume_history)
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Volume confirmation logic
            volume_confirmed = volume_ratio >= 1.2  # 120% of average
            volume_spike = volume_ratio >= self.volume_spike_threshold  # 150% of average
            
            # Volume strength calculation
            if volume_spike:
                volume_strength = min(0.9, 0.5 + (volume_ratio - 1.5) * 0.2)
            elif volume_confirmed:
                volume_strength = 0.5 + (volume_ratio - 1.2) * 0.3
            else:
                volume_strength = max(0.1, volume_ratio * 0.4)
            
            # Volume analysis description
            if volume_spike:
                analysis = 'volume_spike'
            elif volume_confirmed:
                analysis = 'volume_confirmed'
            elif volume_ratio > 0.8:
                analysis = 'normal_volume'
            else:
                analysis = 'low_volume'
            
            return {
                'volume_available': True,
                'volume_confirmation': volume_confirmed,
                'volume_spike': volume_spike,
                'volume_analysis': analysis,
                'volume_strength': round(volume_strength, 3),
                'current_volume': current_volume,
                'average_volume': round(avg_volume, 0),
                'volume_ratio': round(volume_ratio, 2),
                'volume_percentile': self._calculate_volume_percentile(current_volume)
            }
            
        except Exception as e:
            print(f"❌ Volume analysis error: {e}")
            # Fallback on error
            return {
                'volume_available': False,
                'volume_confirmation': True,
                'volume_analysis': 'error_fallback',
                'volume_strength': 0.5,
                'error': str(e)
            }
    
    def _analyze_market_context(self, candles: List[Dict]) -> Dict:
        """
        🌍 วิเคราะห์ market context - COMPLETE
        
        Args:
            candles: รายการแท่งเทียน
            
        Returns:
            Dict: ผลการวิเคราะห์ market context
        """
        try:
            current_time = datetime.now()
            current_candle = candles[-1]
            
            # Trading session detection
            session_info = self._detect_trading_session(current_time)
            
            # Market volatility analysis
            volatility_info = self._analyze_market_volatility(candles)
            
            # Trend analysis (short-term)
            trend_info = self._analyze_short_term_trend(candles)
            
            # Support/Resistance levels
            sr_info = self._analyze_support_resistance(candles)
            
            return {
                **session_info,
                **volatility_info,
                **trend_info,
                **sr_info,
                'market_context_timestamp': current_time,
                'context_quality': self._calculate_context_quality(session_info, volatility_info, trend_info)
            }
            
        except Exception as e:
            print(f"❌ Market context analysis error: {e}")
            return {
                'trading_session': 'unknown',
                'volatility_level': 'medium',
                'trend_direction': 'sideways',
                'context_quality': 0.3
            }
    
    # ==========================================
    # 🔧 HELPER & UTILITY METHODS - COMPLETE  
    # ==========================================
    
    def _validate_connection(self) -> bool:
        """✅ ตรวจสอบการเชื่อมต่อ"""
        try:
            if not self.mt5_connector:
                print("❌ No MT5 connector")
                return False
            
            if not self.mt5_connector.is_connected:
                print("❌ MT5 not connected")
                return False
            
            if not self.symbol:
                print("❌ No symbol specified")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Connection validation error: {e}")
            return False
    
    def _validate_ohlc_data(self, candle: Dict) -> bool:
        """✅ ตรวจสอบความถูกต้องของ OHLC data"""
        try:
            o, h, l, c = candle['open'], candle['high'], candle['low'], candle['close']
            
            # ตรวจสอบว่าเป็นตัวเลข
            if not all(isinstance(x, (int, float)) for x in [o, h, l, c]):
                return False
            
            # ตรวจสอบว่าเป็นค่าบวก
            if not all(x > 0 for x in [o, h, l, c]):
                return False
            
            # ตรวจสอบความสัมพันธ์ OHLC
            if not (l <= min(o, c) <= max(o, c) <= h):
                return False
            
            # ตรวจสอบว่า high >= low
            if h < l:
                return False
            
            return True
            
        except Exception as e:
            return False
    
    def _validate_basic_candle_data(self, candle: Dict) -> bool:
        """✅ ตรวจสอบข้อมูลพื้นฐานของแท่งเทียน"""
        try:
            required_fields = ['time', 'open', 'high', 'low', 'close']
            
            for field in required_fields:
                if field not in candle:
                    return False
            
            return self._validate_ohlc_data(candle)
            
        except Exception as e:
            return False
    
    def _enhance_candle_data(self, candle: Dict) -> Dict:
        """🔧 เพิ่มข้อมูลเสริมให้แท่งเทียน"""
        try:
            enhanced = candle.copy()
            
            # เพิ่ม datetime ถ้ายังไม่มี
            if 'datetime' not in enhanced:
                enhanced['datetime'] = datetime.fromtimestamp(candle['time'])
            
            # คำนวณข้อมูลเสริม
            o, h, l, c = candle['open'], candle['high'], candle['low'], candle['close']
            
            enhanced.update({
                'range': h - l,
                'body_size': abs(c - o),
                'upper_shadow': h - max(o, c),
                'lower_shadow': min(o, c) - l,
                'is_bullish': c > o,
                'is_bearish': c < o,
                'midpoint': (h + l) / 2,
                'typical_price': (h + l + c) / 3
            })
            
            return enhanced
            
        except Exception as e:
            print(f"❌ Enhance candle data error: {e}")
            return candle
    
    def _generate_candle_signature(self, candle: Dict) -> str:
        """🔑 สร้าง signature สำหรับแท่งเทียน"""
        try:
            timestamp = candle['time']
            close_price = candle['close']
            
            # สร้าง signature ที่ unique
            signature = f"CANDLE_{timestamp}_{close_price:.2f}_{candle.get('tick_volume', 0)}"
            
            return signature
            
        except Exception as e:
            return f"CANDLE_ERROR_{int(time.time())}"
    
    def _is_already_processed(self, signature: str) -> bool:
        """🔒 ตรวจสอบว่า signature นี้ถูกประมวลผลแล้วหรือยัง"""
        try:
            is_processed = signature in self.processed_signatures
            
            if not is_processed:
                # เพิ่มใน set และทำความสะอาดถ้าจำเป็น
                self.processed_signatures.add(signature)
                
                if len(self.processed_signatures) > self.max_signature_history:
                    # เก็บแค่ 400 signatures ล่าสุด
                    signatures_list = list(self.processed_signatures)
                    self.processed_signatures = set(signatures_list[-400:])
            
            return is_processed
            
        except Exception as e:
            print(f"❌ Signature check error: {e}")
            return False
    
    def _record_successful_analysis(self, signature: str, analysis: Dict):
        """📝 บันทึกการวิเคราะห์ที่สำเร็จ"""
        try:
            # บันทึก signature
            self.processed_signatures.add(signature)
            
            # บันทึกลง persistence ถ้ามี
            if self.persistence_manager:
                self.persistence_manager.save_processed_signatures(self.processed_signatures)
            
            # อัพเดท cache
            self.cached_analysis = analysis
            self.last_analysis_time = datetime.now()
            
        except Exception as e:
            print(f"❌ Record successful analysis error: {e}")
    
    def _update_volume_tracking(self, candles: List[Dict]):
        """📊 อัพเดท volume tracking"""
        try:
            if not candles:
                return
            
            # ดึง volume จากแท่งล่าสุด
            latest_volumes = []
            
            for candle in candles[-self.max_volume_history:]:
                volume = candle.get('real_volume', 0)
                if volume > 0:
                    latest_volumes.append(volume)
            
            if latest_volumes:
                self.volume_history = latest_volumes
                self.avg_volume = statistics.mean(latest_volumes)
                self.volume_available = True
                
                print(f"📊 Volume updated: {len(latest_volumes)} samples, avg: {self.avg_volume:.0f}")
            else:
                self.volume_available = False
                print(f"📊 No volume data available")
                
        except Exception as e:
            print(f"❌ Volume tracking error: {e}")
            self.volume_available = False
    
    def _record_pattern_occurrence(self, pattern: Dict):
        """📈 บันทึกการเกิด pattern"""
        try:
            pattern_name = pattern['pattern_name']
            
            if pattern_name not in self.pattern_success_rates:
                self.pattern_success_rates[pattern_name] = {
                    'occurrences': 0,
                    'total_strength': 0.0,
                    'avg_strength': 0.0
                }
            
            stats = self.pattern_success_rates[pattern_name]
            stats['occurrences'] += 1
            stats['total_strength'] += pattern['pattern_strength']
            stats['avg_strength'] = stats['total_strength'] / stats['occurrences']
            
            # เก็บ history (จำกัดที่ 100)
            self.pattern_history.append({
                'timestamp': datetime.now(),
                'pattern_name': pattern_name,
                'strength': pattern['pattern_strength']
            })
            
            if len(self.pattern_history) > 100:
                self.pattern_history = self.pattern_history[-100:]
                
        except Exception as e:
            print(f"❌ Pattern recording error: {e}")
    
    def _calculate_analysis_strength(self, basic: Dict, comparison: Dict, pattern: Dict, volume: Dict) -> float:
        """💪 คำนวณความแรงของการวิเคราะห์"""
        try:
            # Base strength from pattern
            pattern_strength = pattern.get('pattern_strength', 0.5)
            pattern_confidence = pattern.get('pattern_confidence', 0.5)
            
            # Volume contribution
            volume_strength = volume.get('volume_strength', 0.5)
            volume_weight = 0.3 if volume.get('volume_available') else 0.1
            
            # Body ratio contribution
            body_ratio = basic.get('body_ratio', 0.3)
            body_strength = min(body_ratio * 1.5, 1.0)  # Cap at 1.0
            
            # Comparison strength
            comparison_strength = 0.5
            if comparison.get('comparison_available'):
                momentum = comparison.get('momentum', 'weak')
                comparison_strength = 0.7 if momentum == 'strong' else 0.5
            
            # Calculate weighted average
            weights = {
                'pattern': 0.4,
                'volume': volume_weight,
                'body': 0.2,
                'comparison': 0.3 - (volume_weight - 0.1)  # Adjust for volume weight
            }
            
            total_strength = (
                pattern_strength * pattern_confidence * weights['pattern'] +
                volume_strength * weights['volume'] +
                body_strength * weights['body'] +
                comparison_strength * weights['comparison']
            )
            
            return round(min(total_strength, 1.0), 3)
            
        except Exception as e:
            print(f"❌ Analysis strength calculation error: {e}")
            return 0.5
    
    def _calculate_analysis_quality(self, candles: List[Dict]) -> float:
        """🎯 คำนวณคุณภาพของการวิเคราะห์"""
        try:
            quality_score = 0.5  # Base score
            
            # Data quantity factor
            data_factor = min(len(candles) / 10.0, 1.0)  # Full score at 10+ candles
            quality_score += data_factor * 0.2
            
            # Volume availability factor
            if self.volume_available:
                quality_score += 0.1
            
            # Time consistency factor
            if self.analysis_count > 0:
                success_rate = self.successful_analysis / self.analysis_count
                quality_score += success_rate * 0.2
            
            return round(min(quality_score, 1.0), 3)
            
        except Exception as e:
            return 0.5
    
    def _detect_trading_session(self, current_time: datetime) -> Dict:
        """🌍 ตรวจจับ trading session"""
        try:
            hour = current_time.hour
            
            # Convert to major trading sessions (approximate)
            if 1 <= hour < 9:
                session = 'asian'
                session_activity = 'medium'
            elif 9 <= hour < 17:
                session = 'london'
                session_activity = 'high'
            elif 17 <= hour <= 23:
                session = 'newyork'
                session_activity = 'high'
            else:
                session = 'quiet'
                session_activity = 'low'
            
            # Overlap periods
            overlap = None
            if 9 <= hour < 11:
                overlap = 'london_asian'
            elif 17 <= hour < 19:
                overlap = 'london_newyork'
            
            return {
                'trading_session': session,
                'session_activity': session_activity,
                'session_overlap': overlap,
                'session_hour': hour
            }
            
        except Exception as e:
            return {
                'trading_session': 'unknown',
                'session_activity': 'medium'
            }
    
    def _analyze_market_volatility(self, candles: List[Dict]) -> Dict:
        """📊 วิเคราะห์ความผันผวนของตลาด"""
        try:
            if len(candles) < 5:
                return {'volatility_level': 'unknown', 'volatility_score': 0.5}
            
            # คำนวณ average range ของ 5 แท่งล่าสุด
            recent_ranges = []
            for candle in candles[-5:]:
                range_val = candle['high'] - candle['low']
                recent_ranges.append(range_val)
            
            avg_range = statistics.mean(recent_ranges)
            current_range = candles[-1]['high'] - candles[-1]['low']
            
            # Volatility assessment
            volatility_ratio = current_range / avg_range if avg_range > 0 else 1.0
            
            if volatility_ratio >= 1.5:
                volatility_level = 'high'
                volatility_score = 0.8
            elif volatility_ratio >= 1.2:
                volatility_level = 'medium_high'
                volatility_score = 0.7
            elif volatility_ratio >= 0.8:
                volatility_level = 'medium'
                volatility_score = 0.5
            else:
                volatility_level = 'low'
                volatility_score = 0.3
            
            return {
                'volatility_level': volatility_level,
                'volatility_score': volatility_score,
                'volatility_ratio': round(volatility_ratio, 2),
                'current_range': round(current_range, 4),
                'avg_range': round(avg_range, 4)
            }
            
        except Exception as e:
            return {
                'volatility_level': 'medium',
                'volatility_score': 0.5
            }
    
    def _analyze_short_term_trend(self, candles: List[Dict]) -> Dict:
        """📈 วิเคราะห์เทรนด์ระยะสั้น"""
        try:
            if len(candles) < 3:
                return {'trend_direction': 'sideways', 'trend_strength': 0.5}
            
            # ใช้ 3 แท่งล่าสุดในการกำหนดเทรนด์
            closes = [candle['close'] for candle in candles[-3:]]
            
            # คำนวณการเปลี่ยนแปลง
            change1 = closes[1] - closes[0]
            change2 = closes[2] - closes[1]
            total_change = closes[2] - closes[0]
            
            # กำหนดทิศทาง
            threshold = 0.0005  # Threshold สำหรับทองคำ
            
            if total_change > threshold and change1 > 0 and change2 > 0:
                trend_direction = 'bullish'
                trend_strength = 0.8
            elif total_change < -threshold and change1 < 0 and change2 < 0:
                trend_direction = 'bearish'
                trend_strength = 0.8
            elif abs(total_change) > threshold:
                if total_change > 0:
                    trend_direction = 'bullish_weak'
                    trend_strength = 0.6
                else:
                    trend_direction = 'bearish_weak'
                    trend_strength = 0.6
            else:
                trend_direction = 'sideways'
                trend_strength = 0.4
            
            return {
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'total_change': round(total_change, 5),
                'trend_consistency': 1.0 if (change1 > 0) == (change2 > 0) else 0.5
            }
            
        except Exception as e:
            return {
                'trend_direction': 'sideways',
                'trend_strength': 0.5
            }
    
    def _analyze_support_resistance(self, candles: List[Dict]) -> Dict:
        """📊 วิเคราะห์ Support/Resistance ระยะสั้น"""
        try:
            if len(candles) < 5:
                return {'sr_analysis': 'insufficient_data'}
            
            # ใช้ high/low ของ 5 แท่งล่าสุด
            highs = [candle['high'] for candle in candles[-5:]]
            lows = [candle['low'] for candle in candles[-5:]]
            
            current = candles[-1]
            current_close = current['close']
            
            # หา potential resistance (highest high)
            max_high = max(highs)
            resistance_distance = abs(current_close - max_high)
            
            # หา potential support (lowest low)
            min_low = min(lows)
            support_distance = abs(current_close - min_low)
            
            # กำหนดระดับความใกล้
            close_threshold = 0.002  # สำหรับทองคำ
            
            near_resistance = resistance_distance < close_threshold
            near_support = support_distance < close_threshold
            
            # คำนวณ position ในช่วง
            range_size = max_high - min_low
            position_in_range = (current_close - min_low) / range_size if range_size > 0 else 0.5
            
            return {
                'sr_analysis': 'available',
                'resistance_level': round(max_high, 4),
                'support_level': round(min_low, 4),
                'near_resistance': near_resistance,
                'near_support': near_support,
                'position_in_range': round(position_in_range, 2),
                'range_size': round(range_size, 4)
            }
            
        except Exception as e:
            return {'sr_analysis': 'error'}
    
    def _calculate_volume_percentile(self, current_volume: float) -> float:
        """📊 คำนวณ volume percentile"""
        try:
            if not self.volume_history or len(self.volume_history) < 5:
                return 50.0  # Default middle percentile
            
            sorted_volumes = sorted(self.volume_history)
            
            # หาตำแหน่งของ current_volume
            position = 0
            for vol in sorted_volumes:
                if current_volume > vol:
                    position += 1
                else:
                    break
            
            percentile = (position / len(sorted_volumes)) * 100
            return round(percentile, 1)
            
        except Exception as e:
            return 50.0
    
    def _calculate_context_quality(self, session_info: Dict, volatility_info: Dict, trend_info: Dict) -> float:
        """🎯 คำนวณคุณภาพของ context"""
        try:
            quality_score = 0.3  # Base score
            
            # Session quality
            activity = session_info.get('session_activity', 'medium')
            if activity == 'high':
                quality_score += 0.3
            elif activity == 'medium':
                quality_score += 0.2
            else:
                quality_score += 0.1
            
            # Volatility contribution
            vol_level = volatility_info.get('volatility_level', 'medium')
            if vol_level in ['medium', 'medium_high']:
                quality_score += 0.2
            elif vol_level == 'high':
                quality_score += 0.1
            else:
                quality_score += 0.05
            
            # Trend clarity
            trend_strength = trend_info.get('trend_strength', 0.5)
            quality_score += trend_strength * 0.2
            
            return round(min(quality_score, 1.0), 2)
            
        except Exception as e:
            return 0.5
    
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
            'candle_color': 'neutral',
            'body_ratio': 0.1,
            'pattern_name': 'error',
            'pattern_strength': 0.0,
            'analysis_strength': 0.0,
            'volume_confirmation': True,  # Fallback confirmation
            'trading_session': 'unknown',
            'volatility_level': 'medium',
            'trend_direction': 'sideways',
            'error': True,
            'timestamp': int(time.time()),
            'datetime': datetime.now()
        }
    
    # ==========================================
    # 📊 STATISTICS & MONITORING METHODS
    # ==========================================
    
    def get_analysis_statistics(self) -> Dict:
        """📊 สถิติการทำงาน"""
        try:
            total_attempts = self.analysis_count
            success_rate = (self.successful_analysis / total_attempts * 100) if total_attempts > 0 else 0
            block_rate = (self.duplicate_blocks / total_attempts * 100) if total_attempts > 0 else 0
            
            return {
                'total_analysis_attempts': total_attempts,
                'successful_analysis': self.successful_analysis,
                'duplicate_blocks': self.duplicate_blocks,
                'time_order_errors': self.time_order_errors,
                'invalid_data_errors': self.invalid_data_errors,
                'success_rate_percent': round(success_rate, 1),
                'block_rate_percent': round(block_rate, 1),
                'signatures_tracked': len(self.processed_signatures),
                'volume_available': self.volume_available,
                'avg_volume': round(self.avg_volume, 0) if self.volume_available else 0,
                'cache_valid': self._is_cache_valid(),
                'last_analysis': self.last_analysis_time.isoformat() if self.last_analysis_time != datetime.min else 'Never'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_pattern_statistics(self) -> Dict:
        """📈 สถิติ patterns"""
        try:
            if not self.pattern_success_rates:
                return {'message': 'No pattern data available'}
            
            # เรียงตามจำนวนครั้งที่เกิด
            sorted_patterns = sorted(
                self.pattern_success_rates.items(),
                key=lambda x: x[1]['occurrences'],
                reverse=True
            )
            
            pattern_stats = {}
            for pattern_name, stats in sorted_patterns[:10]:  # Top 10
                pattern_stats[pattern_name] = {
                    'occurrences': stats['occurrences'],
                    'avg_strength': round(stats['avg_strength'], 3),
                    'total_strength': round(stats['total_strength'], 3)
                }
            
            return {
                'total_patterns_tracked': len(self.pattern_success_rates),
                'pattern_history_count': len(self.pattern_history),
                'top_patterns': pattern_stats,
                'most_frequent': sorted_patterns[0][0] if sorted_patterns else 'none'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def force_cache_refresh(self):
        """🔄 บังคับ refresh cache"""
        try:
            self.cached_analysis = None
            self.last_analysis_time = datetime.min
            print(f"🔄 Analysis cache force refreshed")
        except Exception as e:
            print(f"❌ Cache refresh error: {e}")
    
    def clear_processed_signatures(self, confirm: bool = False):
        """🗑️ ล้าง processed signatures"""
        if not confirm:
            print("❌ Signature clearing aborted: confirm=False")
            return False
        
        try:
            old_count = len(self.processed_signatures)
            self.processed_signatures.clear()
            print(f"🗑️ Cleared {old_count} processed signatures")
            return True
        except Exception as e:
            print(f"❌ Clear signatures error: {e}")
            return False
    
    def reset_statistics(self):
        """🔄 รีเซ็ตสถิติ"""
        try:
            self.analysis_count = 0
            self.duplicate_blocks = 0
            self.successful_analysis = 0
            self.time_order_errors = 0
            self.invalid_data_errors = 0
            self.pattern_history.clear()
            self.pattern_success_rates.clear()
            
            print("🔄 Analysis statistics reset")
            
        except Exception as e:
            print(f"❌ Reset statistics error: {e}")
    
    # ==========================================
    # 🔧 CONFIGURATION & MANAGEMENT
    # ==========================================
    
    def update_configuration(self, new_config: Dict):
        """⚙️ อัพเดทการตั้งค่า"""
        try:
            # อัพเดทการตั้งค่าพื้นฐาน
            if 'symbol' in new_config:
                self.symbol = new_config['symbol']
            
            if 'cache_duration_seconds' in new_config:
                self.cache_duration_seconds = max(1, int(new_config['cache_duration_seconds']))
            
            if 'doji_threshold' in new_config:
                self.doji_threshold = max(0.01, min(0.2, float(new_config['doji_threshold'])))
            
            if 'strong_body_threshold' in new_config:
                self.strong_body_threshold = max(0.3, min(0.9, float(new_config['strong_body_threshold'])))
            
            if 'volume_confirmation_enabled' in new_config:
                self.volume_confirmation_enabled = bool(new_config['volume_confirmation_enabled'])
            
            if 'strict_time_checking' in new_config:
                self.strict_time_checking = bool(new_config['strict_time_checking'])
            
            # Force cache refresh after config change
            self.force_cache_refresh()
            
            print(f"⚙️ Configuration updated")
            
        except Exception as e:
            print(f"❌ Configuration update error: {e}")
    
    def get_current_configuration(self) -> Dict:
        """⚙️ ดึงการตั้งค่าปัจจุบัน"""
        return {
            'symbol': self.symbol,
            'timeframe': 'M1',
            'cache_duration_seconds': self.cache_duration_seconds,
            'min_candles_required': self.min_candles_required,
            'max_candles_lookback': self.max_candles_lookback,
            'doji_threshold': self.doji_threshold,
            'strong_body_threshold': self.strong_body_threshold,
            'volume_confirmation_enabled': self.volume_confirmation_enabled,
            'volume_fallback_enabled': self.volume_fallback_enabled,
            'strict_time_checking': self.strict_time_checking,
            'real_time_mode': self.real_time_mode,
            'max_signature_history': self.max_signature_history
        }
    
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
            'version': '2.0.0',
            'symbol': self.symbol,
            'timeframe': 'M1',
            'features': [
                'OHLC Data Collection',
                'Pattern Recognition',
                'Volume Analysis',
                'Market Context Analysis',
                'Real-time Processing',
                'Duplicate Prevention',
                'Performance Tracking',
                'Persistence Integration'
            ],
            'status': {
                'ready': self.is_ready(),
                'volume_available': self.volume_available,
                'cache_valid': self._is_cache_valid(),
                'persistence_connected': self.persistence_manager is not None
            },
            'configuration': self.get_current_configuration(),
            'statistics': self.get_analysis_statistics()
        }
    
    def get_debug_info(self) -> Dict:
        """🔍 ข้อมูล debug สำหรับ troubleshooting"""
        try:
            return {
                'analyzer_status': {
                    'is_ready': self.is_ready(),
                    'mt5_connected': self.mt5_connector.is_connected if self.mt5_connector else False,
                    'symbol': self.symbol,
                    'timeframe': 'M1'
                },
                'cache_info': {
                    'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time != datetime.min else 'Never',
                    'last_candle_time': self.last_analyzed_candle_time.isoformat() if self.last_analyzed_candle_time != datetime.min else 'Never',
                    'cache_valid': self._is_cache_valid(),
                    'cache_duration': self.cache_duration_seconds
                },
                'signature_tracking': {
                    'processed_count': len(self.processed_signatures),
                    'max_history': self.max_signature_history,
                    'recent_signatures': list(self.processed_signatures)[-5:] if self.processed_signatures else []
                },
                'performance': {
                    'total_analysis': self.analysis_count,
                    'duplicate_blocks': self.duplicate_blocks,
                    'successful_analysis': self.successful_analysis,
                    'block_rate': round((self.duplicate_blocks / self.analysis_count * 100) if self.analysis_count > 0 else 0, 1),
                    'success_rate': round((self.successful_analysis / self.analysis_count * 100) if self.analysis_count > 0 else 0, 1)
                },
                'volume_info': {
                    'available': self.volume_available,
                    'history_count': len(self.volume_history),
                    'avg_volume': round(self.avg_volume, 0) if self.volume_available else 0
                },
                'pattern_info': {
                    'patterns_tracked': len(self.pattern_success_rates),
                    'pattern_history': len(self.pattern_history)
                },
                'error_tracking': {
                    'time_order_errors': self.time_order_errors,
                    'invalid_data_errors': self.invalid_data_errors
                }
            }
            
        except Exception as e:
            return {'debug_error': str(e)}
    
    # ==========================================
    # 💾 PERSISTENCE INTEGRATION
    # ==========================================
    
    def save_to_persistence(self) -> bool:
        """💾 บันทึกข้อมูลลง persistence"""
        try:
            if not self.persistence_manager:
                return False
            
            # บันทึก processed signatures
            success = self.persistence_manager.save_processed_signatures(self.processed_signatures)
            
            if success:
                print("💾 Analyzer data saved to persistence")
            
            return success
            
        except Exception as e:
            print(f"❌ Save to persistence error: {e}")
            return False
    
    def load_from_persistence(self) -> bool:
        """📂 โหลดข้อมูลจาก persistence"""
        try:
            if not self.persistence_manager:
                return False
            
            # โหลด processed signatures
            loaded_signatures = self.persistence_manager.load_processed_signatures()
            
            if loaded_signatures:
                self.processed_signatures.update(loaded_signatures)
                print(f"📂 Loaded {len(loaded_signatures)} processed signatures")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Load from persistence error: {e}")
            return False