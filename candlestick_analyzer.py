"""
🕯️ Smart Candlestick Analyzer - Compatible with Mini Trend System
candlestick_analyzer.py

🔧 UPDATED FOR SMART SIGNAL GENERATOR:
✅ เพิ่ม candle_timestamp สำหรับ signature
✅ เพิ่ม symbol field
✅ ปรับ data format ให้ตรงกับ mini trend analysis
✅ คง method names เดิมไว้ 100%
✅ เพิ่ม multi-candle support
✅ ปรับปรุง error handling

🚀 Features:
✅ OHLC Data Collection & Validation  
✅ Candlestick Pattern Recognition
✅ Volume Analysis with Fallback
✅ Body Ratio & Wick Analysis
✅ Price Direction Detection
✅ Real-time Processing
✅ Signature-based Duplicate Prevention
✅ Mini Trend Data Preparation
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import time
import statistics

class CandlestickAnalyzer:
    """
    🕯️ Smart Candlestick Analyzer
    
    วิเคราะห์แท่งเทียนแบบครบถ้วน รองรับ Mini Trend Analysis
    เตรียมข้อมูลสำหรับ Smart Signal Generator
    """
    
    def __init__(self, mt5_connector, config: Dict):
        """
        🔧 เริ่มต้น Smart Candlestick Analyzer
        
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
        self.min_candles_required = 3  # สำหรับ mini trend
        self.max_candles_lookback = 20
        self.volume_lookback_periods = 10
        
        # Pattern recognition settings
        self.doji_threshold = 0.05
        self.strong_body_threshold = 0.6
        self.hammer_wick_ratio = 2.0
        self.shooting_star_ratio = 2.0
        
        # Volume analysis settings
        self.volume_spike_threshold = 1.5
        self.volume_confirmation_enabled = config.get("volume", {}).get("enabled", True)
        self.volume_fallback_enabled = True
        
        # 🔧 CACHE MANAGEMENT
        self.last_analysis_time = datetime.min
        self.last_analyzed_candle_time = datetime.min
        self.cache_duration_seconds = 5
        self.cached_analysis = None
        
        # 🔧 VOLUME TRACKING
        self.volume_available = False
        self.volume_history = []
        self.max_volume_history = 20
        self.avg_volume = 0.0
        
        # 🆕 SIGNATURE TRACKING สำหรับ mini trend
        self.processed_signatures = set()
        self.max_signature_history = 500
        
        # 🆕 CANDLE STATE TRACKING
        self.last_candle_signature = None
        self.last_processed_candle_time = datetime.min
        self.minimum_time_gap_seconds = 30
        
        # 🆕 PERFORMANCE TRACKING
        self.analysis_count = 0
        self.successful_analysis = 0
        self.error_count = 0
        self.avg_analysis_time = 0.0
        
        print(f"🕯️ Smart Candlestick Analyzer initialized")
        print(f"   Symbol: {self.symbol}")
        print(f"   Timeframe: M1")
        print(f"   Mini trend support: {self.min_candles_required} candles")
        print(f"   Cache duration: {self.cache_duration_seconds}s")
    
    # ==========================================
    # 🎯 MAIN ANALYSIS METHOD (คงชื่อเดิม)
    # ==========================================
    
    def get_current_analysis(self) -> Optional[Dict]:
        """
        🎯 วิเคราะห์แท่งเทียนปัจจุบัน - Enhanced for Mini Trend
        
        คงชื่อ method เดิม แต่เพิ่มข้อมูลสำหรับ Smart Signal Generator
        
        Returns:
            Dict: ข้อมูลการวิเคราะห์ + fields ใหม่สำหรับ mini trend
        """
        try:
            analysis_start = time.time()
            
            if not self._is_ready_for_analysis():
                return None
            
            # ตรวจสอบ cache (เดิม)
            if self._is_cache_valid():
                return self.cached_analysis
            
            # ดึงข้อมูล candles
            candles_data = self._get_candles_for_analysis()
            if not candles_data or len(candles_data) < self.min_candles_required:
                print(f"❌ ไม่เพียงพอสำหรับ analysis: {len(candles_data) if candles_data else 0} candles")
                return None
            
            # วิเคราะห์แท่งปัจจุบัน (เดิม + ปรับปรุง)
            current_candle = candles_data[-1]  # แท่งล่าสุด
            analysis_result = self._analyze_single_candle(current_candle, candles_data)
            
            if not analysis_result:
                return None
            
            # 🆕 เพิ่มข้อมูล meta สำหรับ Smart Signal Generator
            analysis_result.update({
                'symbol': self.symbol,
                'timeframe': 'M1',
                'candle_timestamp': int(current_candle['timestamp']),
                'analysis_timestamp': datetime.now(),
                'total_candles_analyzed': len(candles_data),
                'analyzer_version': 'smart_v2.0'
            })
            
            # บันทึก cache
            self.cached_analysis = analysis_result
            self.last_analysis_time = datetime.now()
            self.last_analyzed_candle_time = datetime.fromtimestamp(current_candle['timestamp'])
            
            # อัพเดทสถิติ
            analysis_time = time.time() - analysis_start
            self._update_performance_stats(analysis_time, True)
            
            print(f"🕯️ Analysis completed for {self.symbol}")
            print(f"   Candle: {analysis_result['candle_color']} body {analysis_result['body_ratio']:.3f}")
            print(f"   Timestamp: {analysis_result['candle_timestamp']}")
            print(f"   Analysis time: {analysis_time*1000:.1f}ms")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Current analysis error: {e}")
            self._update_performance_stats(0, False)
            return None
    
    # ==========================================
    # 🆕 ENHANCED DATA COLLECTION
    # ==========================================
    
    def _get_candles_for_analysis(self) -> Optional[List[Dict]]:
        """
        🔍 ดึงข้อมูล candles สำหรับ analysis - Enhanced
        
        ดึงข้อมูลหลายแท่งเพื่อรองรับ mini trend analysis
        """
        try:
            if not self.mt5_connector.is_connected:
                print(f"❌ MT5 ไม่ได้เชื่อมต่อ")
                return None
            
            # ดึงข้อมูล rates จาก MT5
            candle_count = max(self.min_candles_required, 5)  # ดึงอย่างน้อย 5 แท่ง
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, candle_count)
            
            if rates is None:
                print(f"❌ ไม่สามารถดึง rates สำหรับ {self.symbol}")
                return None
            
            if len(rates) < self.min_candles_required:
                print(f"❌ Rates ไม่เพียงพอ: {len(rates)} < {self.min_candles_required}")
                return None
            
            # แปลงเป็น format ที่ใช้งาน - ใช้แท่งปิดแล้วเท่านั้น
            candles = []
            for i, rate in enumerate(rates[:-1]):
                try:
                    candle = {
                        'timestamp': int(rate[0]),  # rates[i][0] = timestamp
                        'open': float(rate[1]),     # rates[i][1] = open
                        'high': float(rate[2]),     # rates[i][2] = high
                        'low': float(rate[3]),      # rates[i][3] = low
                        'close': float(rate[4]),    # rates[i][4] = close
                        'volume': int(rate[5]) if len(rate) > 5 else 0,  # rates[i][5] = volume
                        'real_volume': int(rate[6]) if len(rate) > 6 else 0
                    }
                    
                    # คำนวณ derived values
                    self._calculate_candle_properties(candle)
                    candles.append(candle)
                    
                except Exception as e:
                    print(f"⚠️ Error processing candle {i}: {e}")
                    continue
            
            if len(candles) < self.min_candles_required:
                print(f"❌ Processed closed candles ไม่เพียงพอ: {len(candles)}")
                return None
            
            print(f"🕯️ Successfully processed {len(candles)} CLOSED candles")
            return candles
            
        except Exception as e:
            print(f"❌ Get candles error: {e}")
            return None
    
    def _calculate_candle_properties(self, candle: Dict):
        """
        📐 คำนวณคุณสมบัติของแท่งเทียน - Enhanced
        
        เพิ่มข้อมูลที่ Smart Signal Generator ต้องการ
        """
        try:
            open_price = candle['open']
            high_price = candle['high']
            low_price = candle['low']
            close_price = candle['close']
            
            # Basic calculations
            candle['body_size'] = abs(close_price - open_price)
            candle['range_size'] = high_price - low_price
            candle['upper_wick'] = high_price - max(open_price, close_price)
            candle['lower_wick'] = min(open_price, close_price) - low_price
            
            # Ratios
            if candle['range_size'] > 0:
                candle['body_ratio'] = candle['body_size'] / candle['range_size']
                candle['upper_wick_ratio'] = candle['upper_wick'] / candle['range_size']
                candle['lower_wick_ratio'] = candle['lower_wick'] / candle['range_size']
            else:
                candle['body_ratio'] = 0.0
                candle['upper_wick_ratio'] = 0.0
                candle['lower_wick_ratio'] = 0.0
            
            # Candle color และ type
            candle['candle_color'] = 'green' if close_price > open_price else 'red'
            candle['is_bullish'] = close_price > open_price
            candle['is_bearish'] = close_price < open_price
            candle['is_doji'] = candle['body_ratio'] < self.doji_threshold
            
            # Price movement info (สำหรับ Signal Generator)
            candle['price_change'] = close_price - open_price
            candle['price_change_abs'] = abs(candle['price_change'])
            candle['price_change_percent'] = (candle['price_change'] / open_price) * 100 if open_price > 0 else 0
            
            # 🆕 เพิ่ม fields สำหรับ compatibility
            candle['candle_type'] = self._classify_candle_type(candle)
            
        except Exception as e:
            print(f"❌ Calculate candle properties error: {e}")
    
    def _classify_candle_type(self, candle: Dict) -> str:
        """
        🏷️ จำแนกประเภทแท่งเทียน - Enhanced
        """
        try:
            body_ratio = candle['body_ratio']
            upper_wick_ratio = candle['upper_wick_ratio']  
            lower_wick_ratio = candle['lower_wick_ratio']
            is_bullish = candle['is_bullish']
            
            # Doji patterns
            if body_ratio < self.doji_threshold:
                if upper_wick_ratio > 0.4 and lower_wick_ratio > 0.4:
                    return 'long_legged_doji'
                elif upper_wick_ratio > 0.6:
                    return 'dragonfly_doji'
                elif lower_wick_ratio > 0.6:
                    return 'gravestone_doji'
                else:
                    return 'doji'
            
            # Strong body candles
            elif body_ratio > self.strong_body_threshold:
                if is_bullish:
                    return 'strong_bullish'
                else:
                    return 'strong_bearish'
            
            # Hammer patterns  
            elif lower_wick_ratio > self.hammer_wick_ratio * body_ratio and upper_wick_ratio < body_ratio:
                if is_bullish:
                    return 'hammer_bullish'
                else:
                    return 'hammer_bearish'
            
            # Shooting star patterns
            elif upper_wick_ratio > self.shooting_star_ratio * body_ratio and lower_wick_ratio < body_ratio:
                if is_bullish:
                    return 'shooting_star_bullish'
                else:
                    return 'shooting_star_bearish'
            
            # Regular candles
            else:
                if is_bullish:
                    return 'bullish'
                else:
                    return 'bearish'
                    
        except Exception as e:
            print(f"❌ Candle classification error: {e}")
            return 'unknown'
    
    def _analyze_single_candle(self, current_candle: Dict, all_candles: List[Dict]) -> Optional[Dict]:
        """
        🔍 วิเคราะห์แท่งเทียนเดี่ยว - Enhanced with Context
        
        Args:
            current_candle: แท่งปัจจุบัน
            all_candles: แท่งทั้งหมดสำหรับ context
        """
        try:
            analysis_result = {}
            
            # 1. Basic OHLC data (เดิม + enhanced)
            analysis_result.update({
                'open': current_candle['open'],
                'high': current_candle['high'], 
                'low': current_candle['low'],
                'close': current_candle['close'],
                'volume': current_candle['volume'],
                'timestamp': current_candle['timestamp']
            })
            
            # 2. Calculated properties (เดิม)
            analysis_result.update({
                'body_size': current_candle['body_size'],
                'range_size': current_candle['range_size'],
                'body_ratio': current_candle['body_ratio'],
                'upper_wick': current_candle['upper_wick'],
                'lower_wick': current_candle['lower_wick'],
                'upper_wick_ratio': current_candle['upper_wick_ratio'],
                'lower_wick_ratio': current_candle['lower_wick_ratio']
            })
            
            # 3. Candle classification (เดิม)
            analysis_result.update({
                'candle_color': current_candle['candle_color'],
                'candle_type': current_candle['candle_type'],
                'is_bullish': current_candle['is_bullish'],
                'is_bearish': current_candle['is_bearish'],
                'is_doji': current_candle['is_doji']
            })
            
            # 4. Price direction analysis (เดิม + enhanced)
            if len(all_candles) >= 2:
                previous_candle = all_candles[-2]
                analysis_result.update({
                    'previous_close': previous_candle['close'],
                    'previous_open': previous_candle['open'],
                    'close_vs_previous': 'higher' if current_candle['close'] > previous_candle['close'] else 'lower',
                    'price_direction': 'higher_close' if current_candle['close'] > previous_candle['close'] else 'lower_close',
                    'price_change_from_previous': current_candle['close'] - previous_candle['close'],
                    'price_change_points': abs(current_candle['close'] - previous_candle['close'])
                })
            else:
                analysis_result.update({
                    'previous_close': current_candle['close'],
                    'close_vs_previous': 'same',
                    'price_direction': 'neutral',
                    'price_change_from_previous': 0,
                    'price_change_points': 0
                })
            
            # 5. Volume analysis (เดิม + enhanced)
            volume_analysis = self._analyze_volume(current_candle, all_candles)
            analysis_result.update(volume_analysis)
            
            # 6. 🆕 Multi-candle context สำหรับ Mini Trend
            context_analysis = self._analyze_multi_candle_context(all_candles)
            analysis_result.update(context_analysis)
            
            # 7. 🆕 Market condition assessment
            market_condition = self._assess_market_condition(all_candles)
            analysis_result.update(market_condition)
            
            # 8. Analysis metadata
            analysis_result.update({
                'analysis_quality': self._calculate_analysis_quality(all_candles),
                'analysis_timestamp': datetime.now(),
                'candles_used_count': len(all_candles)
            })
            
            self.successful_analysis += 1
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Single candle analysis error: {e}")
            self.error_count += 1
            return None
    
    # ==========================================
    # 🆕 MULTI-CANDLE ANALYSIS สำหรับ MINI TREND
    # ==========================================
    
    def _analyze_multi_candle_context(self, candles: List[Dict]) -> Dict:
        """
        🔍 วิเคราะห์ context หลายแท่งสำหรับ Mini Trend
        
        Args:
            candles: รายการแท่งเทียนทั้งหมด
            
        Returns:
            Dict: ข้อมูล context สำหรับ mini trend analysis
        """
        try:
            if len(candles) < 3:
                return {'multi_candle_context': 'insufficient_data'}
            
            # เก็บแค่ 3 แท่งล่าสุดสำหรับ mini trend
            recent_3_candles = candles[-3:]
            
            # นับสีแท่งเทียน
            colors = [candle['candle_color'] for candle in recent_3_candles]
            green_count = colors.count('green')
            red_count = colors.count('red')
            
            # วิเคราะห์ pattern
            pattern_analysis = {
                'recent_3_candles_colors': colors,
                'green_count_in_3': green_count,
                'red_count_in_3': red_count,
                'dominant_color': 'green' if green_count > red_count else 'red' if red_count > green_count else 'mixed',
                'trend_consistency': max(green_count, red_count) / 3.0
            }
            
            # เช็คเงื่อนไข mini trend
            current_color = recent_3_candles[-1]['candle_color']
            current_body_ratio = recent_3_candles[-1]['body_ratio']
            min_body_ratio = self.config.get("smart_entry_rules", {}).get("mini_trend", {}).get("min_body_ratio", 0.05)
            
            # Mini trend signals
            mini_trend_signals = {}
            
            # BUY condition: เขียว 2 ใน 3 + แท่งปัจจุบันเขียว + body >= 5%
            if green_count >= 2 and current_color == 'green' and current_body_ratio >= min_body_ratio:
                mini_trend_signals['buy_mini_trend_detected'] = True
                mini_trend_signals['buy_trend_strength'] = self._calculate_mini_trend_strength(recent_3_candles, 'bullish')
                print(f"🟢 Mini trend BUY detected: {colors}")
            else:
                mini_trend_signals['buy_mini_trend_detected'] = False
            
            # SELL condition: แดง 2 ใน 3 + แท่งปัจจุบันแดง + body >= 5%  
            if red_count >= 2 and current_color == 'red' and current_body_ratio >= min_body_ratio:
                mini_trend_signals['sell_mini_trend_detected'] = True
                mini_trend_signals['sell_trend_strength'] = self._calculate_mini_trend_strength(recent_3_candles, 'bearish')
                print(f"🔴 Mini trend SELL detected: {colors}")
            else:
                mini_trend_signals['sell_mini_trend_detected'] = False
            
            # รวมข้อมูล
            return {
                'multi_candle_context': pattern_analysis,
                'mini_trend_signals': mini_trend_signals
            }
            
        except Exception as e:
            print(f"❌ Multi-candle context error: {e}")
            return {'multi_candle_context': 'error'}
    
    def _calculate_mini_trend_strength(self, candles: List[Dict], direction: str) -> float:
        """
        💪 คำนวณความแข็งแกร่งของ mini trend
        """
        try:
            if len(candles) < 3:
                return 0.5
            
            strength = 0.5  # Base strength
            
            # 1. Consistency factor (แท่งสีเดียวกันเยอะ = แรง)
            target_color = 'green' if direction == 'bullish' else 'red'
            same_color_count = sum(1 for c in candles if c['candle_color'] == target_color)
            consistency_factor = same_color_count / len(candles)
            strength += consistency_factor * 0.3
            
            # 2. Body size factor (แท่งใหญ่ = แรง)
            avg_body_ratio = sum(c['body_ratio'] for c in candles) / len(candles)
            body_factor = min(avg_body_ratio * 2, 0.2)
            strength += body_factor
            
            # 3. Price movement factor
            total_movement = abs(candles[-1]['close'] - candles[0]['open'])
            movement_factor = min(total_movement / 2.0, 0.2)  # สูงสุด +0.2
            strength += movement_factor
            
            return round(min(strength, 1.0), 3)
            
        except Exception as e:
            print(f"❌ Mini trend strength error: {e}")
            return 0.5
    
    # ==========================================
    # 🔧 VOLUME ANALYSIS (เดิม + ปรับปรุง)
    # ==========================================
    
    def _analyze_volume(self, current_candle: Dict, all_candles: List[Dict]) -> Dict:
        """
        📊 วิเคราะห์ volume - Enhanced with better fallback
        """
        try:
            volume_result = {
                'volume_available': False,
                'volume_factor': 1.0,
                'volume_analysis': 'unavailable',
                'avg_volume': 0
            }
            
            current_volume = current_candle.get('volume', 0)
            
            # ตรวจสอบว่ามี volume data หรือไม่
            if current_volume > 0 and len(all_candles) >= 5:
                
                # คำนวณ average volume
                volumes = [c.get('volume', 0) for c in all_candles[-10:] if c.get('volume', 0) > 0]
                
                if volumes and len(volumes) >= 3:
                    avg_volume = statistics.mean(volumes)
                    self.avg_volume = avg_volume
                    self.volume_available = True
                    
                    volume_factor = current_volume / avg_volume if avg_volume > 0 else 1.0
                    
                    # Volume classification
                    if volume_factor >= self.volume_spike_threshold:
                        volume_analysis = 'high'
                    elif volume_factor >= 1.2:
                        volume_analysis = 'above_average' 
                    elif volume_factor <= 0.8:
                        volume_analysis = 'below_average'
                    else:
                        volume_analysis = 'normal'
                    
                    volume_result.update({
                        'volume_available': True,
                        'volume_factor': round(volume_factor, 2),
                        'volume_analysis': volume_analysis,
                        'avg_volume': round(avg_volume, 0)
                    })
                    
                    print(f"📊 Volume: {current_volume:,} (avg: {avg_volume:,.0f}, factor: {volume_factor:.2f})")
                
            else:
                # Volume fallback - ใช้ราคาและ range แทน
                if self.volume_fallback_enabled:
                    volume_result.update({
                        'volume_available': False,
                        'volume_factor': self._estimate_volume_from_price_action(current_candle, all_candles),
                        'volume_analysis': 'estimated_from_price',
                        'avg_volume': 0
                    })
                    print(f"📊 Volume fallback used")
            
            return volume_result
            
        except Exception as e:
            print(f"❌ Volume analysis error: {e}")
            return {
                'volume_available': False,
                'volume_factor': 1.0,
                'volume_analysis': 'error',
                'avg_volume': 0
            }
    
    def _estimate_volume_from_price_action(self, current_candle: Dict, all_candles: List[Dict]) -> float:
        """
        📊 ประมาณ volume จาก price action เมื่อไม่มี volume data
        """
        try:
            # ใช้ range size และ body ratio เป็นตัวแทน
            range_size = current_candle['range_size']
            body_ratio = current_candle['body_ratio']
            
            # คำนวณ average range จากแท่งก่อนหน้า
            recent_ranges = [c['range_size'] for c in all_candles[-5:]]
            avg_range = statistics.mean(recent_ranges) if recent_ranges else range_size
            
            # ประมาณ volume factor
            range_factor = range_size / avg_range if avg_range > 0 else 1.0
            body_factor = min(body_ratio * 2, 1.5)  # แท่งใหญ่ = volume เยอะ
            
            estimated_factor = (range_factor + body_factor) / 2
            return round(max(0.5, min(estimated_factor, 2.0)), 2)
            
        except Exception as e:
            return 1.0
    
    # ==========================================
    # 🆕 MARKET CONDITION ASSESSMENT
    # ==========================================
    
    def _assess_market_condition(self, candles: List[Dict]) -> Dict:
        """
        🌍 ประเมินสภาวะตลาด - สำหรับ Smart Decision Making
        """
        try:
            condition_result = {
                'market_condition': 'unknown',
                'volatility_level': 'medium',
                'trend_direction': 'sideways',
                'session_info': {}
            }
            
            if len(candles) < 5:
                return condition_result
            
            # 1. วิเคราะห์ volatility
            recent_ranges = [c['range_size'] for c in candles[-5:]]
            avg_range = statistics.mean(recent_ranges)
            current_range = candles[-1]['range_size']
            
            volatility_ratio = current_range / avg_range if avg_range > 0 else 1.0
            
            if volatility_ratio >= 2.0:
                volatility_level = 'very_high'
            elif volatility_ratio >= 1.5:
                volatility_level = 'high'
            elif volatility_ratio >= 1.2:
                volatility_level = 'above_normal'
            elif volatility_ratio <= 0.6:
                volatility_level = 'low' 
            else:
                volatility_level = 'normal'
            
            # 2. วิเคราะห์ trend direction
            closes = [c['close'] for c in candles[-5:]]
            if len(closes) >= 2:
                overall_change = closes[-1] - closes[0]
                if abs(overall_change) < avg_range * 0.5:
                    trend_direction = 'sideways'
                elif overall_change > 0:
                    trend_direction = 'uptrend'
                else:
                    trend_direction = 'downtrend'
            
            # 3. Session information  
            session_info = self._detect_trading_session(datetime.now())
            
            condition_result.update({
                'volatility_level': volatility_level,
                'volatility_ratio': round(volatility_ratio, 2),
                'trend_direction': trend_direction,
                'session_info': session_info,
                'market_condition': f"{volatility_level}_{trend_direction}"
            })
            
            return condition_result
            
        except Exception as e:
            print(f"❌ Market condition assessment error: {e}")
            return {'market_condition': 'error'}
    
    def _detect_trading_session(self, current_time: datetime) -> Dict:
        """🌍 ตรวจจับ trading session"""
        try:
            hour = current_time.hour
            
            if 1 <= hour < 9:
                session = 'asian'
                activity = 'medium'
            elif 9 <= hour < 17:
                session = 'london'
                activity = 'high'
            elif 17 <= hour <= 23:
                session = 'newyork'
                activity = 'high'
            else:
                session = 'quiet'
                activity = 'low'
            
            # Overlap detection
            overlap = None
            if 9 <= hour < 11:
                overlap = 'london_asian'
            elif 17 <= hour < 19:
                overlap = 'london_newyork'
            
            return {
                'trading_session': session,
                'session_activity': activity,
                'session_overlap': overlap,
                'current_hour': hour
            }
            
        except Exception as e:
            return {'trading_session': 'unknown', 'session_activity': 'medium'}
    
    # ==========================================
    # 🔧 UTILITY METHODS (เดิม + ปรับปรุง)
    # ==========================================
    
    def _is_ready_for_analysis(self) -> bool:
        """✅ ตรวจสอบความพร้อมสำหรับ analysis"""
        try:
            if not self.mt5_connector or not self.mt5_connector.is_connected:
                print(f"❌ MT5 not connected")
                return False
            
            # ตรวจสอบ symbol
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                print(f"❌ Symbol {self.symbol} not found")
                return False
            
            if not symbol_info.visible:
                print(f"📊 Symbol ไม่ visible - attempting to select...")
                if not mt5.symbol_select(self.symbol, True):
                    print(f"❌ ไม่สามารถ select symbol {self.symbol}")
                    return False
                print(f"✅ Symbol selected successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ Readiness check error: {e}")
            return False
    
    def _is_cache_valid(self) -> bool:
        """⏰ ตรวจสอบ cache validity"""
        try:
            if not self.cached_analysis:
                return False
            
            time_diff = (datetime.now() - self.last_analysis_time).total_seconds()
            return time_diff < self.cache_duration_seconds
            
        except Exception:
            return False
    
    def _update_performance_stats(self, analysis_time: float, success: bool):
        """📊 อัพเดทสถิติการทำงาน"""
        try:
            self.analysis_count += 1
            
            if success:
                self.successful_analysis += 1
                
                # อัพเดท average analysis time
                if self.avg_analysis_time == 0:
                    self.avg_analysis_time = analysis_time
                else:
                    self.avg_analysis_time = (self.avg_analysis_time * 0.9) + (analysis_time * 0.1)
            else:
                self.error_count += 1
                
        except Exception as e:
            print(f"❌ Performance stats update error: {e}")
    
    def _calculate_analysis_quality(self, candles: List[Dict]) -> float:
        """🎯 คำนวณคุณภาพการวิเคราะห์"""
        try:
            quality_score = 0.5
            
            # Data quantity factor
            data_factor = min(len(candles) / 10.0, 1.0)
            quality_score += data_factor * 0.2
            
            # Volume availability
            if self.volume_available:
                quality_score += 0.1
            
            # Success rate factor
            if self.analysis_count > 0:
                success_rate = self.successful_analysis / self.analysis_count
                quality_score += success_rate * 0.2
            
            return round(min(quality_score, 1.0), 3)
            
        except Exception as e:
            return 0.5
    
    # ==========================================
    # 🔧 MAINTENANCE & INFO METHODS (เดิม)
    # ==========================================
    
    def clear_cache(self):
        """🗑️ ล้าง cache"""
        self.cached_analysis = None
        self.last_analysis_time = datetime.min
        print(f"🗑️ Analysis cache cleared")
    
    def get_analysis_statistics(self) -> Dict:
        """📊 สถิติการวิเคราะห์"""
        try:
            return {
                'total_analysis': self.analysis_count,
                'successful_analysis': self.successful_analysis,
                'error_count': self.error_count,
                'success_rate': self.successful_analysis / max(self.analysis_count, 1),
                'avg_analysis_time_ms': round(self.avg_analysis_time * 1000, 2),
                'volume_available': self.volume_available,
                'processed_signatures_count': len(self.processed_signatures)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def is_ready(self) -> bool:
        """✅ ตรวจสอบความพร้อม"""
        return (
            self.mt5_connector is not None and
            self.mt5_connector.is_connected and
            self.symbol is not None
        )
    
    def get_analyzer_info(self) -> Dict:
        """ℹ️ ข้อมูล Analyzer"""
        return {
            'name': 'Smart Candlestick Analyzer',
            'version': '3.0.0-SmartFreq', 
            'symbol': self.symbol,
            'timeframe': 'M1',
            'features': [
                'Multi-candle Analysis',
                'Mini Trend Detection', 
                'Volume Analysis with Fallback',
                'Market Condition Assessment',
                'Real-time Processing',
                'Smart Caching System'
            ],
            'status': {
                'ready': self.is_ready(),
                'volume_available': self.volume_available,
                'cache_valid': self._is_cache_valid()
            },
            'statistics': self.get_analysis_statistics()
        }