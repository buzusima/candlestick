"""
🎯 Smart Frequent Signal Generator - Mini Trend + Portfolio Balance
signal_generator.py

🚀 NEW FEATURES:
✅ Mini Trend Analysis (2 ใน 3 แท่ง)
✅ Portfolio Balance Intelligence  
✅ Dynamic Signal Strength
✅ Quality Filters (ป้องกันมั่วซั่ว)
✅ Session-based Frequency Adjustment
✅ คงชื่อ method เดิมไว้ 100%

📋 NEW BUY Signal Rules:
- แท่งเขียว 2 ใน 3 แท่งล่าสุด
- Body ratio >= 5% (ลดจาก 10%)
- การเคลื่อนไหว >= 0.2 points
- Portfolio balance consideration

📋 NEW SELL Signal Rules:  
- แท่งแดง 2 ใน 3 แท่งล่าสุด
- Body ratio >= 5% (ลดจาก 10%)
- การเคลื่อนไหว >= 0.2 points
- Portfolio balance consideration
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import MetaTrader5 as mt5

class SignalGenerator:
    """
    🎯 Smart Frequent Signal Generator
    
    สร้างสัญญาณ BUY/SELL แบบ Mini Trend Analysis
    พร้อม Portfolio Balance และ Dynamic Lot Sizing
    """
    
    def __init__(self, candlestick_analyzer, config: Dict):
        """
        🔧 เริ่มต้น Smart Signal Generator
        
        Args:
            candlestick_analyzer: Candlestick analyzer instance  
            config: การตั้งค่าระบบใหม่
        """
        self.candlestick_analyzer = candlestick_analyzer
        self.config = config
        
        # การตั้งค่า signal generation ใหม่
        self.smart_rules = config.get("smart_entry_rules", {})
        self.mini_trend_config = self.smart_rules.get("mini_trend", {})
        self.balance_config = self.smart_rules.get("portfolio_balance", {})
        self.lot_config = self.smart_rules.get("dynamic_lot_sizing", {})
        self.filter_config = config.get("entry_filters", {})
        
        # Signal rate limiting (อัพเดทแล้ว)
        trading_config = config.get("trading", {})
        self.cooldown_seconds = trading_config.get("signal_cooldown_seconds", 60)
        self.max_signals_per_hour = trading_config.get("max_signals_per_hour", 80)
        self.high_frequency_mode = trading_config.get("high_frequency_mode", True)
        
        # Signal tracking (เดิม)
        self.last_signal_time = datetime.min
        self.signal_history = []
        self.total_signals_today = 0
        self.last_reset_date = datetime.now().date()
        
        # Performance tracking (เดิม)
        self.signals_generated = {'BUY': 0, 'SELL': 0, 'WAIT': 0}
        self.signal_quality_scores = []
        
        # Signal locking (เดิม)
        self.last_signal_signature = None
        self.signal_signatures = set()
        self.max_signal_history = 100
        
        # 🆕 NEW: Portfolio tracking
        self.portfolio_stats = {
            'buy_positions': 0,
            'sell_positions': 0,
            'last_update': datetime.min
        }
        
        # 🆕 NEW: Mini trend tracking
        self.trend_history = []
        self.max_trend_history = 10
        
        print(f"🎯 Smart Signal Generator initialized")
        print(f"   Mode: Smart Frequent Entry")
        print(f"   Cooldown: {self.cooldown_seconds}s")
        print(f"   Max signals/hour: {self.max_signals_per_hour}")
        print(f"   Mini trend: {self.mini_trend_config.get('lookback_candles', 3)} candles")
        print(f"   Body ratio: {self.mini_trend_config.get('min_body_ratio', 0.05)*100:.1f}%")
    
    # ==========================================
    # 🎯 MAIN SIGNAL GENERATION (คงชื่อเดิม)
    # ==========================================
    
    def generate_signal(self, candlestick_data: Dict) -> Optional[Dict]:
        """
        🎯 สร้าง Signal แบบ Smart Frequent Entry
        
        คงชื่อ method เดิมไว้ แต่เปลี่ยน logic เป็น Mini Trend
        """
        try:
            if not candlestick_data:
                return self._create_wait_signal("No data")
            
            # ตรวจสอบ rate limiting (เดิม)
            if not self._check_rate_limits():
                return self._create_wait_signal("Rate limit exceeded")
            
            # ดึง timestamp และ signature check (เดิม)
            candle_timestamp = candlestick_data.get('candle_timestamp')
            if not candle_timestamp:
                return self._create_wait_signal("No timestamp")
            
            signature = f"SIGNAL_{candle_timestamp}"
            if self._is_signal_sent_for_signature(signature):
                return None
            
            # 🆕 NEW: ดึงข้อมูล candles หลายแท่งสำหรับ mini trend
            recent_candles = self._get_recent_candles_data(candlestick_data)
            if not recent_candles or len(recent_candles) < 3:
                return self._create_wait_signal("Insufficient candle data")
            
            # 🆕 NEW: อัพเดท portfolio stats
            self._update_portfolio_stats()
            
            # 🆕 NEW: Mini Trend Analysis
            trend_signal = self._analyze_mini_trend(recent_candles)
            if not trend_signal:
                return self._create_wait_signal("No mini trend detected")
            
            # 🆕 NEW: Quality Filters
            if not self._pass_quality_filters(recent_candles, trend_signal):
                return self._create_wait_signal("Failed quality filters")
            
            # 🆕 NEW: Portfolio Balance Adjustment
            adjusted_signal = self._apply_portfolio_balance(trend_signal)
            if not adjusted_signal:
                return self._create_wait_signal("Portfolio balance blocked")
            
            # Lock signal signature
            self._mark_signal_sent_for_signature(signature)
            
            # สร้าง final signal
            signal = {
                'action': adjusted_signal['action'],
                'strength': adjusted_signal['strength'],
                'confidence': adjusted_signal['confidence'],
                'timestamp': datetime.now(),
                'signal_id': f"{adjusted_signal['action']}_{candle_timestamp}",
                'candle_timestamp': candle_timestamp,
                'close': recent_candles[-1]['close'],
                'symbol': candlestick_data.get('symbol', 'XAUUSD.v'),
                'mini_trend_strength': adjusted_signal.get('trend_strength', 0),
                'portfolio_balance_factor': adjusted_signal.get('balance_factor', 1.0),
                'dynamic_lot_size': self._calculate_dynamic_lot_size(adjusted_signal)
            }
            
            # บันทึก signal (เดิม)
            self._record_signal(signal)
            
            print(f"🎯 SMART SIGNAL: {signal['action']} (Strength: {signal['strength']:.2f})")
            print(f"   Mini trend: {adjusted_signal.get('trend_pattern', 'unknown')}")
            print(f"   Balance factor: {signal['portfolio_balance_factor']:.2f}")
            print(f"   Dynamic lot: {signal['dynamic_lot_size']:.3f}")
            
            return signal
            
        except Exception as e:
            print(f"❌ Signal generation error: {e}")
            return self._create_wait_signal(f"Error: {str(e)}")
    
    # ==========================================
    # 🆕 NEW: MINI TREND ANALYSIS METHODS
    # ==========================================
    
    def _get_recent_candles_data(self, current_candlestick_data: Dict) -> List[Dict]:
        """
        🔍 ดึงข้อมูล candles หลายแท่งสำหรับ mini trend analysis
        """
        try:
            # ดึงข้อมูลจาก MT5 โดยตรง
            symbol = current_candlestick_data.get('symbol', 'XAUUSD.v')
            timeframe = mt5.TIMEFRAME_M1
            
            # ดึง 5 แท่งล่าสุด (ใช้ 3 แท่ง, เผื่อไว้ 2 แท่ง)
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 5)
            
            if rates is None or len(rates) < 3:
                print(f"❌ ไม่สามารถดึง rates data ได้")
                return []
            
            # แปลงเป็น format ที่ใช้งาน
            candles = []
            for i, rate in enumerate(rates[-3:]):  # ใช้ 3 แท่งล่าสุด
                candle = {
                    'open': float(rate[1]),    # rates[i][1] = open
                    'high': float(rate[2]),    # rates[i][2] = high  
                    'low': float(rate[3]),     # rates[i][3] = low
                    'close': float(rate[4]),   # rates[i][4] = close
                    'volume': int(rate[5]) if len(rate) > 5 else 0,
                    'timestamp': int(rate[0])
                }
                
                # คำนวณ derived data
                candle['body_size'] = abs(candle['close'] - candle['open'])
                candle['range_size'] = candle['high'] - candle['low'] 
                candle['body_ratio'] = candle['body_size'] / candle['range_size'] if candle['range_size'] > 0 else 0
                candle['candle_color'] = 'green' if candle['close'] > candle['open'] else 'red'
                
                candles.append(candle)
            
            print(f"🔍 Retrieved {len(candles)} candles for mini trend analysis")
            return candles
            
        except Exception as e:
            print(f"❌ Get recent candles error: {e}")
            return []
    
    def _analyze_mini_trend(self, candles: List[Dict]) -> Optional[Dict]:
        """
        🔍 วิเคราะห์ Mini Trend จาก 3 แท่งล่าสุด
        """
        try:
            if len(candles) < 3:
                # print(f"❌ ข้อมูลไม่พอ: {len(candles)} แท่ง")
                return None
            
            # วิเคราะห์ 3 แท่งล่าสุด
            colors = [candle['candle_color'] for candle in candles]
            green_count = colors.count('green')
            red_count = colors.count('red')
            
            # แท่งปัจจุบัน (แท่งสุดท้าย)
            current_candle = candles[-1]
            current_body_ratio = current_candle['body_ratio']
            current_color = current_candle['candle_color']
            
            # ตรวจสอบ body ratio ขั้นต่ำ
            min_body_ratio = self.mini_trend_config.get('min_body_ratio', 0.05)
            if current_body_ratio < min_body_ratio:
                # print(f"❌ Body เล็กเกิน: {current_body_ratio:.1%} < {min_body_ratio:.1%}")
                return None
            
            # print(f"\n📊 MINI TREND: {colors}")
            # print(f"   🟢 เขียว: {green_count}  🔴 แดง: {red_count}")
            # print(f"   📏 Body ปัจจุบัน: {current_body_ratio:.1%}")
            
            # 🎯 BUY Signal: เขียว 2 ใน 3 + แท่งปัจจุบันเขียว
            if green_count >= 2 and current_color == 'green':
                trend_strength = self._calculate_trend_strength(candles, 'bullish')
                # print(f"🎯 BUY TREND ตรวจพบ! (แรง: {trend_strength:.1%})")
                
                signal = {
                    'action': 'BUY',
                    'strength': trend_strength,
                    'confidence': min(0.6 + (green_count - 2) * 0.2, 0.9),
                    'trend_pattern': f"GREEN_{green_count}_of_3",
                    'trend_strength': trend_strength,
                    'candles_analyzed': len(candles)
                }
                
                return signal
            
            # 🎯 SELL Signal: แดง 2 ใน 3 + แท่งปัจจุบันแดง  
            if red_count >= 2 and current_color == 'red':
                trend_strength = self._calculate_trend_strength(candles, 'bearish')
                # print(f"🎯 SELL TREND ตรวจพบ! (แรง: {trend_strength:.1%})")
                
                signal = {
                    'action': 'SELL',
                    'strength': trend_strength, 
                    'confidence': min(0.6 + (red_count - 2) * 0.2, 0.9),
                    'trend_pattern': f"RED_{red_count}_of_3",
                    'trend_strength': trend_strength,
                    'candles_analyzed': len(candles)
                }
                
                return signal
            
            # print(f"⏸️  ไม่มี Mini Trend (เขียว:{green_count} แดง:{red_count})")
            return None
            
        except Exception as e:
            print(f"❌ Mini trend error: {e}")
            return None
    
    def _calculate_trend_strength(self, candles: List[Dict], direction: str) -> float:
        """
        📊 คำนวณความแข็งแกร่งของ trend - ENHANCED WITH DETAILED LOGS (FIXED)
        
        5 Factors Analysis:
        1. Pattern Consistency (40%) - แท่งต่อเนื่องสีเดียวกัน
        2. Body Strength (25%) - ความใหญ่และคุณภาพของ body
        3. Momentum (20%) - ความเร็วและทิศทางราคา
        4. Volume Confirmation (10%) - volume สนับสนุนทิศทาง
        5. Market Context (5%) - เงื่อนไขโดยรวม
        """
        try:
            print(f"\n🔍 ENHANCED CALCULATION START: {direction}")
            
            if len(candles) < 3:
                return 0.5
            
            strength = 0.1  # Base strength ต่ำ
            
            # Calculate basic variables first
            colors = [candle['candle_color'] for candle in candles]
            target_color = 'green' if direction == 'bullish' else 'red'
            same_color_count = colors.count(target_color)
            green_count = colors.count('green')  # Define here
            red_count = colors.count('red')      # Define here
            
            # =============================================
            # 1. PATTERN CONSISTENCY ANALYSIS (40% weight)
            # =============================================
            if same_color_count == 3:      # Perfect pattern
                pattern_score = 0.40
                pattern_desc = "Perfect 3/3"
            elif same_color_count == 2:   # Good pattern
                pattern_score = 0.25
                pattern_desc = "Good 2/3"
                # Bonus for consecutive candles
                if candles[-2]['candle_color'] == candles[-1]['candle_color'] == target_color:
                    pattern_score += 0.05
                    pattern_desc += " +consecutive"
            else:                         # Weak pattern
                pattern_score = 0.05
                pattern_desc = "Weak 1/3"
            
            strength += pattern_score
            print(f"   🎨 Pattern: {pattern_desc} → +{pattern_score:.3f}")
            
            # =============================================
            # 2. BODY STRENGTH ANALYSIS (25% weight)
            # =============================================
            body_ratios = [candle['body_ratio'] for candle in candles]
            avg_body_ratio = sum(body_ratios) / len(body_ratios)
            current_body = candles[-1]['body_ratio']
            
            # Body quality scoring
            if avg_body_ratio >= 0.7:      # Very strong bodies
                body_score = 0.25
                body_desc = "Very strong"
            elif avg_body_ratio >= 0.5:   # Strong bodies
                body_score = 0.20
                body_desc = "Strong"
            elif avg_body_ratio >= 0.3:   # Medium bodies
                body_score = 0.15
                body_desc = "Medium"
            elif avg_body_ratio >= 0.15:  # Weak bodies
                body_score = 0.08
                body_desc = "Weak"
            elif avg_body_ratio >= 0.05:  # Very weak
                body_score = 0.03
                body_desc = "Very weak"
            else:                          # Doji-like
                body_score = -0.05
                body_desc = "Doji penalty"
            
            # Current candle body bonus/penalty
            if current_body >= 0.8:
                current_bonus = 0.05
                body_desc += " +strong_current"
            elif current_body < 0.03:
                current_bonus = -0.08
                body_desc += " -weak_current"
            else:
                current_bonus = 0.0
            
            total_body_score = body_score + current_bonus
            strength += total_body_score
            print(f"   💪 Body: {body_desc} (avg={avg_body_ratio:.3f}, curr={current_body:.3f}) → +{total_body_score:.3f}")
            
            # =============================================
            # 3. MOMENTUM ANALYSIS (20% weight)
            # =============================================
            price_momentum = abs(candles[-1]['close'] - candles[0]['close'])
            
            # Momentum scoring - ปรับสำหรับ M5
            if price_momentum >= 15.0:     # Very strong movement (5x)
                momentum_score = 0.20
                momentum_desc = "Very strong"
            elif price_momentum >= 10.0:  # Strong movement (5x)
                momentum_score = 0.15
                momentum_desc = "Strong"
            elif price_momentum >= 5.0:   # Medium movement (5x)
                momentum_score = 0.10
                momentum_desc = "Medium"
            elif price_momentum >= 2.5:   # Weak movement (5x)
                momentum_score = 0.05
                momentum_desc = "Weak"
            else:                          # Very weak
                momentum_score = -0.02
                momentum_desc = "Too weak"

            # Acceleration check
            if len(candles) >= 3:
                step1_change = abs(candles[1]['close'] - candles[0]['close'])
                step2_change = abs(candles[2]['close'] - candles[1]['close'])
                
                if step1_change > 0:  # Avoid division by zero
                    if step2_change > step1_change * 1.3:
                        accel_bonus = 0.03
                        momentum_desc += " +accelerating"
                    elif step2_change < step1_change * 0.7:
                        accel_bonus = -0.02
                        momentum_desc += " -decelerating"
                    else:
                        accel_bonus = 0.0
                else:
                    accel_bonus = 0.0
            else:
                accel_bonus = 0.0
            
            total_momentum = momentum_score + accel_bonus
            strength += total_momentum
            print(f"   🚀 Momentum: {momentum_desc} ({price_momentum:.2f}pts) → +{total_momentum:.3f}")
            
            # =============================================
            # 4. VOLUME CONFIRMATION (10% weight)
            # =============================================
            current_candle = candles[-1]
            volume_score = 0.0
            volume_desc = "No data"
            
            if 'volume' in current_candle and current_candle['volume'] > 0:
                prev_volumes = [c.get('volume', 1) for c in candles[:-1] if c.get('volume', 0) > 0]
                
                if prev_volumes:
                    avg_prev_volume = sum(prev_volumes) / len(prev_volumes)
                    current_volume = current_candle['volume']
                    volume_ratio = current_volume / max(avg_prev_volume, 1)
                    
                    if volume_ratio >= 2.5:     # Volume explosion
                        volume_score = 0.10
                        volume_desc = f"Explosion ({volume_ratio:.1f}x)"
                    elif volume_ratio >= 1.8:  # High volume
                        volume_score = 0.06
                        volume_desc = f"High ({volume_ratio:.1f}x)"
                    elif volume_ratio >= 1.3:  # Moderate increase
                        volume_score = 0.03
                        volume_desc = f"Moderate ({volume_ratio:.1f}x)"
                    elif volume_ratio >= 0.8:  # Normal
                        volume_score = 0.01
                        volume_desc = f"Normal ({volume_ratio:.1f}x)"
                    else:                       # Low volume
                        volume_score = -0.03
                        volume_desc = f"Low ({volume_ratio:.1f}x)"
            
            strength += volume_score
            print(f"   📊 Volume: {volume_desc} → +{volume_score:.3f}")
            
            # =============================================
            # 5. MARKET CONTEXT (5% weight)
            # =============================================
            context_score = 0.0
            context_penalties = []
            
            # Mixed signals penalty
            if direction == 'bullish' and red_count >= 2:
                context_score -= 0.03
                context_penalties.append("mixed_signals")
            elif direction == 'bearish' and green_count >= 2:
                context_score -= 0.03
                context_penalties.append("mixed_signals")
            
            # Weak current candle penalty
            current_body = candles[-1]['body_ratio']
            if current_body < 0.03:
                context_score -= 0.05
                context_penalties.append("weak_current")
            
            # Indecision pattern penalty
            if abs(green_count - red_count) == 0:  # Equal colors
                context_score -= 0.02
                context_penalties.append("indecision")
            
            # Strong continuation bonus
            if same_color_count >= 2 and current_body >= 0.6:
                context_score += 0.03
                context_penalties.append("strong_continuation")
            
            strength += context_score
            context_desc = ", ".join(context_penalties) if context_penalties else "neutral"
            print(f"   🌐 Context: {context_desc} → +{context_score:.3f}")
            
            # =============================================
            # 6. FINAL SCORE CALCULATION
            # =============================================
            final_strength = round(min(max(strength, 0.05), 0.95), 3)
            
            print(f"   📊 CALCULATION SUMMARY:")
            print(f"      Base(0.1) + Pattern({pattern_score:.3f}) + Body({total_body_score:.3f}) + Momentum({total_momentum:.3f}) + Volume({volume_score:.3f}) + Context({context_score:.3f})")
            print(f"   🎯 FINAL {direction.upper()} STRENGTH: {final_strength:.3f}")
            print(f"   📈 Expected lot range: {self._predict_lot_size(final_strength)}")
            
            return final_strength
            
        except Exception as e:
            print(f"❌ Enhanced trend strength error: {e}")
            return 0.5

    def _predict_lot_size(self, strength: float) -> str:
        """🔮 คาดการณ์ lot size ที่จะได้"""
        base_lot = 0.01
        if strength >= 0.9:
            return f"{base_lot * 8:.2f} lots (x8)"
        elif strength >= 0.75:
            return f"{base_lot * 5:.2f} lots (x5)"
        elif strength >= 0.6:
            return f"{base_lot * 3:.2f} lots (x3)"
        elif strength >= 0.45:
            return f"{base_lot * 2:.2f} lots (x2)"
        else:
            return f"{base_lot * 1:.2f} lots (x1)"
            
        # ==========================================
    # 🆕 NEW: PORTFOLIO BALANCE METHODS
    # ==========================================
    
    def _update_portfolio_stats(self):
        """
        📊 อัพเดทสถิติ portfolio (BUY:SELL positions)
        """
        try:
            # ดึงข้อมูล positions จาก MT5
            symbol = self.config.get("trading", {}).get("symbol", "XAUUSD.v")
            positions = mt5.positions_get(symbol=symbol)
            
            if positions is None:
                positions = []
            
            buy_count = len([p for p in positions if p.type == mt5.POSITION_TYPE_BUY])
            sell_count = len([p for p in positions if p.type == mt5.POSITION_TYPE_SELL])
            
            self.portfolio_stats = {
                'buy_positions': buy_count,
                'sell_positions': sell_count,
                'total_positions': len(positions),
                'buy_ratio': buy_count / max(len(positions), 1),
                'sell_ratio': sell_count / max(len(positions), 1),
                'last_update': datetime.now()
            }
            
            # print(f"📊 Portfolio: BUY {buy_count}, SELL {sell_count}")
            
        except Exception as e:
            print(f"❌ Portfolio stats update error: {e}")
            self.portfolio_stats = {'buy_positions': 0, 'sell_positions': 0, 'last_update': datetime.now()}
    
    def _apply_portfolio_balance(self, trend_signal: Dict) -> Optional[Dict]:
        """
        ⚖️ ปรับ signal ตาม portfolio balance
        
        Logic: ถ้าฝั่งหนึ่งเยอะเกิน → ลด probability ของฝั่งนั้น
        """
        try:
            if not self.balance_config.get('enabled', True):
                return trend_signal
            
            action = trend_signal['action']
            buy_ratio = self.portfolio_stats.get('buy_ratio', 0.5)
            
            # ตรวจสอบความไม่สมดุล
            max_imbalance = self.balance_config.get('max_imbalance_ratio', 0.7)
            adjustment_factor = self.balance_config.get('balance_adjustment_factor', 1.5)
            
            balance_factor = 1.0
            
            if buy_ratio > max_imbalance:  # BUY เยอะเกินไป
                if action == 'BUY':
                    balance_factor = 0.3  # ลดโอกาส BUY
                    print(f"⚖️ BUY oversupply ({buy_ratio:.1%}) - reducing BUY signals")
                elif action == 'SELL':  
                    balance_factor = adjustment_factor  # เพิ่มโอกาส SELL
                    print(f"⚖️ Need more SELL - boosting SELL signals")
                    
            elif buy_ratio < (1 - max_imbalance):  # SELL เยอะเกินไป
                if action == 'SELL':
                    balance_factor = 0.3  # ลดโอกาส SELL
                    print(f"⚖️ SELL oversupply ({1-buy_ratio:.1%}) - reducing SELL signals")
                elif action == 'BUY':
                    balance_factor = adjustment_factor  # เพิ่มโอกาส BUY  
                    print(f"⚖️ Need more BUY - boosting BUY signals")
            
            # ปรับ signal strength
            adjusted_strength = trend_signal['strength'] * balance_factor
            
            # ถ้า strength ต่ำเกินไป = block signal
            if adjusted_strength < 0.4:
                print(f"🚫 Signal blocked by balance (strength: {adjusted_strength:.2f})")
                return None
            
            # อัพเดท signal
            trend_signal['strength'] = min(adjusted_strength, 1.0)
            trend_signal['balance_factor'] = balance_factor
            trend_signal['portfolio_state'] = {
                'buy_ratio': buy_ratio,
                'sell_ratio': 1 - buy_ratio,
                'is_balanced': 0.35 <= buy_ratio <= 0.65
            }
            
            return trend_signal
            
        except Exception as e:
            print(f"❌ Portfolio balance error: {e}")
            return trend_signal
    
    def _pass_quality_filters(self, candles: List[Dict], signal: Dict) -> bool:
        """
        🔍 ตรวจสอบ Quality Filters เพื่อป้องกันการเข้าไม้มั่วซั่ว
        """
        try:
            # 1. Price Movement Filter
            movement_filter = self.filter_config.get("price_movement_filter", {})
            if movement_filter.get('enabled', True):
                if not self._check_price_movement_filter(candles):
                    print(f"🚫 Failed price movement filter")
                    return False
            
            # 2. Session Activity Filter  
            session_filter = self.filter_config.get("session_activity_filter", {})
            if session_filter.get('enabled', True):
                if not self._check_session_filter(signal):
                    print(f"🚫 Failed session activity filter")
                    return False
            
            # 3. Volatility Filter
            volatility_filter = self.filter_config.get("volatility_filter", {})
            if volatility_filter.get('enabled', True):
                if not self._check_volatility_filter(candles):
                    print(f"🚫 Failed volatility filter") 
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Quality filter error: {e}")
            return False
    
    def _check_price_movement_filter(self, candles: List[Dict]) -> bool:
        """🔍 ตรวจสอบการเคลื่อนไหวของราคา"""
        try:
            if len(candles) < 2:
                return False
            
            movement_config = self.filter_config.get("price_movement_filter", {})
            min_movement = movement_config.get("min_price_change_points", 0.20)
            max_movement = movement_config.get("max_movement_points", 5.00)
            
            current_close = candles[-1]['close']
            previous_close = candles[-2]['close']
            price_change = abs(current_close - previous_close)
            
            if price_change < min_movement:
                print(f"❌ เคลื่อนไหวน้อย: {price_change:.3f} < {min_movement}")
                return False
            
            if price_change > max_movement:
                print(f"❌ เคลื่อนไหวมาก (Gap?): {price_change:.3f} > {max_movement}")
                return False
            
            print(f"✅ การเคลื่อนไหว OK: {price_change:.3f} points")
            return True
            
        except Exception as e:
            print(f"❌ Movement filter error: {e}")
            return True
    
    def _check_session_filter(self, signal: Dict) -> bool:
        """🕐 ตรวจสอบ session activity"""
        try:
            session_config = self.filter_config.get("session_activity_filter", {})
            
            # ตรวจจับ session ปัจจุบัน
            current_hour = datetime.now().hour
            
            # กำหนด session activity
            if 1 <= current_hour < 9:    # Asian
                activity_level = 'low'
                frequency_multiplier = session_config.get('low_activity_reduction', 0.3)
            elif 9 <= current_hour < 17:  # London  
                activity_level = 'high'
                frequency_multiplier = session_config.get('high_activity_boost', 1.2)
            elif 17 <= current_hour <= 23: # NY
                activity_level = 'high' 
                frequency_multiplier = session_config.get('high_activity_boost', 1.2)
            else:  # Quiet
                activity_level = 'low'
                frequency_multiplier = 0.2
            
            # Overlap bonus
            if 9 <= current_hour < 11 or 17 <= current_hour < 19:
                frequency_multiplier *= session_config.get('overlap_boost', 1.5)
                activity_level = 'overlap'
            
            # Random gate ตาม frequency multiplier  
            import random
            if random.random() > frequency_multiplier:
                print(f"🕐 Session gate: {activity_level} activity blocked signal")
                return False
            
            print(f"✅ Session gate passed: {activity_level} activity")
            signal['session_activity'] = activity_level
            signal['frequency_multiplier'] = frequency_multiplier
            
            return True
            
        except Exception as e:
            print(f"❌ Session filter error: {e}")
            return True
    
    def _check_volatility_filter(self, candles: List[Dict]) -> bool:
        """📈 ตรวจสอบ volatility level"""
        try:
            volatility_config = self.filter_config.get("volatility_filter", {})
            
            # คำนวณ simple volatility จากช่วง high-low
            if len(candles) < 2:
                return True
            
            current_range = candles[-1]['range_size']
            avg_range = sum(c['range_size'] for c in candles) / len(candles)
            
            volatility_ratio = current_range / avg_range if avg_range > 0 else 1.0
            
            low_vol_threshold = volatility_config.get("low_volatility_threshold", 0.5)
            high_vol_threshold = volatility_config.get("high_volatility_threshold", 3.0)
            
            if volatility_ratio < low_vol_threshold:
                print(f"📈 Low volatility: {volatility_ratio:.2f} - may reduce signals")
                # ไม่ block แต่อาจลด strength
                
            elif volatility_ratio > high_vol_threshold:
                print(f"📈 High volatility: {volatility_ratio:.2f} - caution mode") 
                # ไม่ block แต่ระวัง
            
            print(f"✅ Volatility check passed: {volatility_ratio:.2f}")
            return True
            
        except Exception as e:
            print(f"❌ Volatility filter error: {e}")
            return True
    
    # ==========================================
    # 🆕 NEW: DYNAMIC LOT SIZE CALCULATION  
    # ==========================================
    
    def _calculate_dynamic_lot_size(self, signal_data: Dict) -> float:
        """
        📏 คำนวณ Dynamic Lot Size ตาม Multiple Factors
        
        Factors:
        1. Signal Strength (50-300%)
        2. Trend Strength (70-150%)  
        3. Portfolio Balance (60-140%)
        4. Price Movement (80-120%)
        """
        try:
            lot_config = self.lot_config
            base_lot = lot_config.get("base_lot", 0.01)
            min_lot = lot_config.get("min_lot", 0.01)
            max_lot = lot_config.get("max_lot", 0.20)
            
            final_lot = base_lot
            
            # 1. Signal Strength Factor
            strength_config = lot_config.get("signal_strength_factor", {})
            if strength_config.get('enabled', True):
                signal_strength = signal_data.get('strength', 0.5)
                min_mult = strength_config.get('min_multiplier', 0.5)
                max_mult = strength_config.get('max_multiplier', 3.0)
                sensitivity = strength_config.get('strength_sensitivity', 1.2)
                
                strength_multiplier = min_mult + (signal_strength ** sensitivity) * (max_mult - min_mult)
                final_lot *= strength_multiplier
                
                print(f"📊 Signal strength: {signal_strength:.2f} → x{strength_multiplier:.2f}")
            
            # 2. Trend Strength Factor
            trend_config = lot_config.get("trend_strength_factor", {})
            if trend_config.get('enabled', True):
                trend_strength = signal_data.get('trend_strength', 0.5)
                threshold = trend_config.get('trend_threshold', 0.6)
                
                if trend_strength >= threshold:
                    trend_multiplier = trend_config.get('strong_trend_multiplier', 1.5)
                    print(f"💪 Strong trend: x{trend_multiplier:.2f}")
                else:
                    trend_multiplier = trend_config.get('weak_trend_multiplier', 0.7)
                    print(f"📉 Weak trend: x{trend_multiplier:.2f}")
                
                final_lot *= trend_multiplier
            
            # 3. Portfolio Balance Factor
            balance_config = lot_config.get("balance_factor", {})
            if balance_config.get('enabled', True):
                balance_factor = signal_data.get('balance_factor', 1.0)
                
                if balance_factor > 1.0:  # ต้องการเพิ่มฝั่งนี้
                    boost = balance_config.get('imbalance_boost', 1.3)
                    balance_multiplier = min(balance_factor, boost)
                    print(f"⚖️ Balance boost: x{balance_multiplier:.2f}")
                elif balance_factor < 1.0:  # ฝั่งนี้เยอะเกิน
                    reduction = balance_config.get('oversupply_reduction', 0.6)
                    balance_multiplier = max(balance_factor, reduction)
                    print(f"⚖️ Balance reduction: x{balance_multiplier:.2f}")
                else:
                    balance_multiplier = 1.0
                
                final_lot *= balance_multiplier
            
            # 4. Movement Factor
            movement_config = lot_config.get("movement_factor", {})
            if movement_config.get('enabled', True):
                # ใช้ข้อมูลจาก signal ถ้ามี หรือคำนวณใหม่
                movement_factor = self._calculate_movement_factor(signal_data)
                final_lot *= movement_factor
                print(f"📏 Movement factor: x{movement_factor:.2f}")
            
            # ปรับเข้า range ที่กำหนด
            final_lot = max(min_lot, min(final_lot, max_lot))
            final_lot = round(final_lot, 3)  # ปัดเป็น 3 ตำแหน่ง
            
            print(f"💰 Dynamic lot calculated: {final_lot:.3f}")
            return final_lot
            
        except Exception as e:
            print(f"❌ Dynamic lot calculation error: {e}")
            return self.lot_config.get("base_lot", 0.01)
    
    def _calculate_movement_factor(self, signal_data: Dict) -> float:
        """📈 คำนวณ factor จากการเคลื่อนไหวราคา"""
        try:
            movement_config = self.lot_config.get("movement_factor", {})
            min_points = movement_config.get("min_movement_points", 0.20)
            max_points = movement_config.get("max_movement_points", 2.00) 
            max_multiplier = movement_config.get("movement_multiplier_max", 1.4)
            
            # ประมาณการเคลื่อนไหวจาก signal (หรือใช้ default)
            estimated_movement = signal_data.get('price_change', 0.5)  # default 0.5 points
            
            # คำนวณ multiplier
            if estimated_movement <= min_points:
                return 0.8  # movement น้อย = lot น้อย
            elif estimated_movement >= max_points:
                return max_multiplier
            else:
                # Linear interpolation
                ratio = (estimated_movement - min_points) / (max_points - min_points)
                return 0.8 + ratio * (max_multiplier - 0.8)
                
        except Exception as e:
            return 1.0
    
    # ==========================================
    # 🔧 UTILITY METHODS (คงเดิมส่วนใหญ่)
    # ==========================================
    
    def _check_rate_limits(self) -> bool:
        """⏰ ตรวจสอบ rate limiting (เดิม)"""
        try:
            now = datetime.now()
            
            # ตรวจสอบ cooldown
            time_since_last = (now - self.last_signal_time).total_seconds()
            if time_since_last < self.cooldown_seconds:
                return False
            
            # ตรวจสอบสัญญาณต่อชั่วโมง  
            hour_ago = now - timedelta(hours=1)
            recent_signals = [s for s in self.signal_history if s['timestamp'] > hour_ago]
            
            if len(recent_signals) >= self.max_signals_per_hour:
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Rate limit check error: {e}")
            return False
    
    def _create_wait_signal(self, reason: str) -> Dict:
        """สร้าง WAIT signal (เดิม)"""
        return {
            'action': 'WAIT',
            'strength': 0.0,
            'confidence': 0.0,
            'timestamp': datetime.now(),
            'reason': reason,
            'signal_id': f"WAIT_{datetime.now().strftime('%H%M%S')}"
        }
    
    def _is_signal_sent_for_signature(self, signature: str) -> bool:
        """🔒 เช็คว่าส่ง signal แล้วหรือยัง (เดิม)"""
        try:
            if not hasattr(self, 'signal_signatures'):
                self.signal_signatures = set()
            
            return signature in self.signal_signatures
            
        except Exception as e:
            return False
    
    def _mark_signal_sent_for_signature(self, signature: str):
        """🔒 บันทึกว่าส่ง signal แล้ว (เดิม)"""
        try:
            if not hasattr(self, 'signal_signatures'):
                self.signal_signatures = set()
            
            self.signal_signatures.add(signature)
            
            # เก็บแค่ 100 signatures ล่าสุด
            if len(self.signal_signatures) > 100:
                signatures_list = list(self.signal_signatures)
                self.signal_signatures = set(signatures_list[-50:])
            
        except Exception as e:
            print(f"❌ Mark signature error: {e}")
    
    def _record_signal(self, signal_data: Dict):
        """📝 บันทึก Signal History (เดิม)"""
        try:
            if not hasattr(self, 'signals_generated'):
                self.signals_generated = {'BUY': 0, 'SELL': 0, 'WAIT': 0}
            if not hasattr(self, 'signal_history'):
                self.signal_history = []
            if not hasattr(self, 'last_signal_time'):
                self.last_signal_time = datetime.min
                
            action = signal_data.get('action')
            if action in ['BUY', 'SELL']:
                self.signals_generated[action] += 1
                self.signal_history.append({
                    'action': action,
                    'strength': signal_data.get('strength', 0),
                    'timestamp': datetime.now(),
                    'signal_id': signal_data.get('signal_id')
                })
                self.last_signal_time = datetime.now()
                
            print(f"📝 Signal recorded: {action}")
            
        except Exception as e:
            print(f"❌ Record signal error: {e}")

    # ==========================================
    # 🔧 DEBUGGING & MAINTENANCE METHODS (เดิม)
    # ==========================================
    
    def clear_signal_locks(self):
        """🗑️ ล้างการล็อก signal ทั้งหมด (เดิม)"""
        try:
            if hasattr(self, 'signal_signatures'):
                old_count = len(self.signal_signatures)
                self.signal_signatures.clear()
                print(f"🗑️ Cleared {old_count} signal signature locks")
            
            return True
            
        except Exception as e:
            print(f"❌ Clear signal locks error: {e}")
            return False

    def get_signal_lock_info(self) -> Dict:
        """📊 ข้อมูลการล็อก signal (เดิม)"""
        try:
            if not hasattr(self, 'signal_signatures'):
                self.signal_signatures = set()
            
            return {
                'total_locked_signatures': len(self.signal_signatures),
                'recent_signatures': list(self.signal_signatures)[-5:] if self.signal_signatures else [],
                'max_signature_history': 100,
                'lock_method': 'candle_timestamp_based'
            }
            
        except Exception as e:
            return {'error': str(e)}

    def get_portfolio_stats(self) -> Dict:
        """📊 ส่งออกสถิติ portfolio"""
        return self.portfolio_stats

    def get_performance_summary(self) -> Dict:
        """📈 สรุปผลงาน signal generation"""
        try:
            total_signals = sum(self.signals_generated.values())
            
            return {
                'total_signals_generated': total_signals,
                'buy_signals': self.signals_generated.get('BUY', 0),
                'sell_signals': self.signals_generated.get('SELL', 0),
                'wait_signals': self.signals_generated.get('WAIT', 0),
                'buy_sell_ratio': self.signals_generated.get('BUY', 0) / max(self.signals_generated.get('SELL', 1), 1),
                'avg_signal_quality': sum(self.signal_quality_scores) / max(len(self.signal_quality_scores), 1),
                'portfolio_stats': self.portfolio_stats,
                'last_signal_time': self.last_signal_time.isoformat() if self.last_signal_time != datetime.min else None
            }
            
        except Exception as e:
            return {'error': str(e)}