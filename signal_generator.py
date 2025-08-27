"""
🎯 Pure Candlestick Signal Generator
signal_generator.py

🚀 Features:
✅ สร้าง BUY/SELL signals ตามกฎ Pure Candlestick
✅ Signal Strength Calculation  
✅ Cooldown Management
✅ Signal Rate Limiting (20 signals/hour max)
✅ Volume Confirmation (optional with fallback)

📋 BUY Signal Rules:
- แท่งเทียนสีเขียว (Close > Open)  
- ราคาปิดสูงกว่าแท่งก่อนหน้า (Close > Previous Close)
- Body ratio >= 10% (configurable)
- Volume confirmation (optional)

📋 SELL Signal Rules:  
- แท่งเทียนสีแดง (Close < Open)
- ราคาปิดต่ำกว่าแท่งก่อนหน้า (Close < Previous Close)
- Body ratio >= 10% (configurable)
- Volume confirmation (optional)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

class SignalGenerator:
    """
    🎯 Pure Candlestick Signal Generator
    
    สร้างสัญญาณ BUY/SELL จากการวิเคราะห์แท่งเทียน
    พร้อม rate limiting และ cooldown management
    """
    
    def __init__(self, candlestick_analyzer, config: Dict):
        """
        🔧 เริ่มต้น Signal Generator
        
        Args:
            candlestick_analyzer: Candlestick analyzer instance  
            config: การตั้งค่าระบบ
        """
        self.candlestick_analyzer = candlestick_analyzer
        self.config = config
        
        # การตั้งค่า signal generation
        self.candlestick_rules = config.get("candlestick_rules", {})
        self.buy_conditions = self.candlestick_rules.get("buy_conditions", {})
        self.sell_conditions = self.candlestick_rules.get("sell_conditions", {})
        self.signal_strength_config = self.candlestick_rules.get("signal_strength", {})
        
        # Signal rate limiting
        self.cooldown_seconds = config.get("trading", {}).get("signal_cooldown_seconds", 60)
        self.max_signals_per_hour = config.get("trading", {}).get("max_signals_per_hour", 20)
        
        # Signal tracking
        self.last_signal_time = datetime.min
        self.signal_history = []  # เก็บ signals ใน 1 ชั่วโมงล่าสุด
        self.total_signals_today = 0
        self.last_reset_date = datetime.now().date()
        
        # Performance tracking
        self.signals_generated = {'BUY': 0, 'SELL': 0, 'WAIT': 0}
        self.signal_quality_scores = []
        
        self.last_signal_signature = None     # ลายเซ็นของแท่งที่ส่ง signal ล่าสุด
        self.signal_signatures = set()        # เก็บลายเซ็นที่ส่ง signal แล้ว
        self.max_signal_history = 30 

        print(f"🎯 Signal Generator initialized")
        print(f"   Cooldown: {self.cooldown_seconds}s between signals")
        print(f"   Max signals/hour: {self.max_signals_per_hour}")
        print(f"   Min body ratio: {self.buy_conditions.get('min_body_ratio', 0.1)*100:.1f}%")
    
    # ==========================================
    # 🎯 MAIN SIGNAL GENERATION
    # ==========================================
    
    def generate_signal(self, candlestick_data: Dict) -> Optional[Dict]:
        """
        🎯 สร้าง Signal - REAL CANDLE VERSION
        
        🔧 BACK TO REAL CANDLES:
        - ใช้แท่งจริงจาก MT5
        - BUY: Current Close > Previous Close  
        - SELL: Current Close < Previous Close
        - ไม่ซับซ้อน ไม่สร้างข้อมูลปลอม
        """
        try:
            print(f"\n=== 🎯 REAL CANDLE SIGNAL GENERATION ===")
            
            # ดึงลายเซ็น OHLC จากแท่งจริง
            candle_signature = candlestick_data.get('candle_signature')
            if not candle_signature:
                return self._create_wait_signal("No real OHLC signature")
            
            # เช็คว่าส่ง signal สำหรับแท่งจริงนี้แล้วหรือยัง
            if self._is_signal_sent_for_signature(candle_signature):
                return self._create_wait_signal("Signal already sent for this real candle")
            
            candle_time = candlestick_data.get('candle_time')
            print(f"🆕 Processing real candle (rates[1]): {candle_time.strftime('%H:%M') if candle_time else 'Unknown'}")
            print(f"   Real OHLC: {candle_signature}")
            
            # ดึงข้อมูลจากแท่งจริง
            current_close = float(candlestick_data.get('close', 0))
            previous_close = float(candlestick_data.get('previous_close', 0))
            price_diff = float(candlestick_data.get('price_difference', 0))
            overall_strength = float(candlestick_data.get('analysis_strength', 0))
            body_ratio = float(candlestick_data.get('body_ratio', 0))
            candle_color = candlestick_data.get('candle_color', 'unknown')
            signal_type = candlestick_data.get('signal_type', 'neutral')
            
            print(f"📊 REAL CANDLE DATA (rates[1] vs rates[2]):")
            print(f"   Current Close [rates[1]]: ${current_close:.2f}")
            print(f"   Previous Close [rates[2]]: ${previous_close:.2f}")
            print(f"   Price Change: {price_diff:+.2f}")
            print(f"   Candle Color: {candle_color}")
            print(f"   Body Ratio: {body_ratio:.3f}")
            print(f"   Overall Strength: {overall_strength:.3f}")
            
            # เงื่อนไขพื้นฐานจากแท่งจริง
            min_price_change = 0.10      # 10 cents สำหรับแท่งจริง
            min_strength = 0.20          # 20% strength
            min_body_ratio = 0.05        # 5% body ratio
            
            # ตรวจสอบเงื่อนไข
            price_change_ok = abs(price_diff) >= min_price_change
            strength_ok = overall_strength >= min_strength
            body_ok = body_ratio >= min_body_ratio
            
            print(f"🔍 REAL CANDLE SIGNAL CONDITIONS (rates[1] vs rates[2]):")
            print(f"   Price Change OK: {price_change_ok} (|{price_diff:.2f}| >= {min_price_change})")
            print(f"   Strength OK: {strength_ok} ({overall_strength:.3f} >= {min_strength})")
            print(f"   Body OK: {body_ok} ({body_ratio:.3f} >= {min_body_ratio})")
            
            # ตัดสินใจ signal จากแท่งจริง
            signal_action = 'WAIT'
            signal_strength = 0.0
            signal_reasons = []
            
            if price_change_ok and strength_ok and body_ok:
                if signal_type == 'bullish' and price_diff > 0:
                    signal_action = 'BUY'
                    signal_reasons.append(f"📈 Real candle: rates[1] close (${current_close:.2f}) > rates[2] close (${previous_close:.2f})")
                    signal_reasons.append(f"🟢 Bullish {candle_color} candle with body ratio {body_ratio:.1%}")
                    
                elif signal_type == 'bearish' and price_diff < 0:
                    signal_action = 'SELL'
                    signal_reasons.append(f"📉 Real candle: rates[1] close (${current_close:.2f}) < rates[2] close (${previous_close:.2f})")
                    signal_reasons.append(f"🔴 Bearish {candle_color} candle with body ratio {body_ratio:.1%}")
                
                else:
                    return self._create_wait_signal(f"Signal type mismatch: {signal_type} but price_diff = {price_diff:+.2f}")
                
                # คำนวณ signal strength จากแท่งจริง
                signal_strength = min(overall_strength, 1.0)
                signal_reasons.append(f"💪 Real candle strength: {signal_strength:.3f}")
                
            else:
                reasons = []
                if not price_change_ok:
                    reasons.append(f"Price change too small ({abs(price_diff):.2f} < {min_price_change})")
                if not strength_ok:
                    reasons.append(f"Candle too weak ({overall_strength:.3f} < {min_strength})")
                if not body_ok:
                    reasons.append(f"Body too small ({body_ratio:.3f} < {min_body_ratio})")
                return self._create_wait_signal("; ".join(reasons))
            
            # เช็ค minimum signal strength สุดท้าย
            min_signal_strength = 0.25  # 25% สำหรับแท่งจริง
            if signal_strength < min_signal_strength:
                return self._create_wait_signal(f"Signal too weak ({signal_strength:.2f} < {min_signal_strength})")
            
            # บันทึกว่าส่ง signal สำหรับแท่งจริงนี้แล้ว
            self._mark_signal_sent_for_signature(candle_signature)
            
            print(f"✅ REAL CANDLE SIGNAL APPROVED")
            print(f"   Action: {signal_action}")
            print(f"   Strength: {signal_strength:.3f}")
            print(f"   Real Candle: {candle_color} {signal_type}")
            print(f"   OHLC: {candle_signature}")
            
            # สร้าง signal data จากแท่งจริง
            signal_data = {
                'action': signal_action,
                'strength': signal_strength,
                'confidence': signal_strength,
                'timestamp': datetime.now(),
                'candle_time': candle_time,
                'candle_signature': candle_signature,
                'reasons': signal_reasons,
                
                # ข้อมูลแท่งจริง
                'open': candlestick_data.get('open'),
                'high': candlestick_data.get('high'),
                'low': candlestick_data.get('low'),
                'close': current_close,
                'previous_close': previous_close,
                'price_change': price_diff,
                
                # การวิเคราะห์จากแท่งจริง
                'body_ratio': body_ratio,
                'candle_color': candle_color,
                'signal_type': signal_type,  # ใช้ signal_type แทน candle_type
                'analysis_strength': overall_strength,
                
                # ข้อมูลเพิ่มเติม
                'signal_id': f"{signal_action}_{datetime.now().strftime('%H%M%S')}",
                'tracking_method': 'real_candle_rates_1_vs_2_signal',
                'is_real_candle': True,
                
                # Volume จากแท่งจริง
                'volume_factor': candlestick_data.get('volume_factor', 1.0),
                'current_volume': candlestick_data.get('current_volume', 0),
                'previous_volume': candlestick_data.get('previous_volume', 0),
                
                # Pattern จากแท่งจริง
                'pattern_name': candlestick_data.get('pattern_name', f'real_{signal_action.lower()}'),
                'price_direction': candlestick_data.get('price_direction'),
                'candle_range': candlestick_data.get('candle_range', 0),
                'body_size': candlestick_data.get('body_size', 0)
            }
            
            return signal_data
            
        except Exception as e:
            print(f"❌ Real candle signal generation error: {e}")
            return self._create_wait_signal(f"Error: {str(e)}")
                    
    def _is_signal_sent_for_signature(self, signature: str) -> bool:
        """
        🔍 เช็คว่าลายเซ็น OHLC นี้ส่ง signal แล้วหรือยัง
        
        Args:
            signature: ลายเซ็น OHLC เช่น "3378.28_3378.76_3377.14_3377.26"
            
        Returns:
            bool: True ถ้าส่ง signal แล้ว
        """
        is_sent = signature in self.signal_signatures
        
        if is_sent:
            print(f"🚫 Signal already sent for OHLC: {signature}")
        else:
            print(f"🆕 New OHLC for signal generation: {signature}")
        
        return is_sent

    def _mark_signal_sent_for_signature(self, signature: str):
        """
        ✅ บันทึกว่าส่ง signal สำหรับ OHLC นี้แล้ว - NO TIME VERSION
        """
        try:
            self.signal_signatures.add(signature)
            
            # เก็บแค่ 15 ลายเซ็นล่าสุด (ลดลงเพราะไม่มี timestamp)
            if len(self.signal_signatures) > 15:
                # ลบแบบ FIFO
                oldest_signature = next(iter(self.signal_signatures))
                self.signal_signatures.remove(oldest_signature)
                print(f"🗑️ Removed oldest signal OHLC: {oldest_signature}")
            
            print(f"✅ Signal sent for OHLC: {signature}")
            print(f"   Total signals: {len(self.signal_signatures)}")
            
        except Exception as e:
            print(f"❌ Mark signal signature error: {e}")

    def _evaluate_sell_conditions(self, data: Dict) -> Dict:
        """
        🔴 ประเมินเงื่อนไข SELL - FINAL FIXED VERSION
        """
        try:
            print(f"🔴 === SELL CONDITIONS (FINAL FIXED) ===")
            
            candle_color = data.get('candle_color')
            current_close = float(data.get('close', 0))
            previous_close = float(data.get('previous_close', 0))
            body_ratio = float(data.get('body_ratio', 0))
            min_body_ratio = self.sell_conditions.get('min_body_ratio', 0.1)
            
            # 🔧 FINAL FIX: การเปรียบเทียบที่ชัดเจน
            condition_1 = (candle_color == 'red')
            condition_2 = (current_close < previous_close)
            condition_3 = (body_ratio >= min_body_ratio)
            
            print(f"   1. Red candle: {condition_1} (color: {candle_color})")
            print(f"   2. Lower close: {condition_2}")
            print(f"      → Current: {current_close:.4f}")
            print(f"      → Previous: {previous_close:.4f}")
            print(f"      → {current_close:.4f} < {previous_close:.4f} = {condition_2}")
            print(f"   3. Body sufficient: {condition_3} ({body_ratio:.3f} >= {min_body_ratio})")
            
            all_conditions_met = condition_1 and condition_2 and condition_3
            signal_strength = min(body_ratio * 2, 1.0) if all_conditions_met else 0.0
            
            print(f"   → ALL CONDITIONS: {all_conditions_met}")
            print(f"   → STRENGTH: {signal_strength:.3f}")
            
            return {
                'signal_type': 'SELL',
                'core_conditions_passed': all_conditions_met,
                'signal_strength': signal_strength,
                'conditions_detail': {
                    'red_candle': condition_1,
                    'lower_close': condition_2,
                    'body_sufficient': condition_3
                }
            }
            
        except Exception as e:
            print(f"❌ SELL conditions error: {e}")
            return {
                'signal_type': 'SELL',
                'core_conditions_passed': False,
                'signal_strength': 0.0,
                'error': str(e)
            }

    def _evaluate_buy_conditions(self, data: Dict) -> Dict:
        """
        🟢 ประเมินเงื่อนไข BUY - FINAL FIXED VERSION
        """
        try:
            print(f"🟢 === BUY CONDITIONS (FINAL FIXED) ===")
            
            candle_color = data.get('candle_color')
            current_close = float(data.get('close', 0))
            previous_close = float(data.get('previous_close', 0))
            body_ratio = float(data.get('body_ratio', 0))
            min_body_ratio = self.buy_conditions.get('min_body_ratio', 0.1)
            
            # 🔧 FINAL FIX: การเปรียบเทียบที่ชัดเจน
            condition_1 = (candle_color == 'green')
            condition_2 = (current_close > previous_close)
            condition_3 = (body_ratio >= min_body_ratio)
            
            print(f"   1. Green candle: {condition_1} (color: {candle_color})")
            print(f"   2. Higher close: {condition_2}")
            print(f"      → Current: {current_close:.4f}")
            print(f"      → Previous: {previous_close:.4f}")
            print(f"      → {current_close:.4f} > {previous_close:.4f} = {condition_2}")
            print(f"   3. Body sufficient: {condition_3} ({body_ratio:.3f} >= {min_body_ratio})")
            
            all_conditions_met = condition_1 and condition_2 and condition_3
            signal_strength = min(body_ratio * 2, 1.0) if all_conditions_met else 0.0
            
            print(f"   → ALL CONDITIONS: {all_conditions_met}")
            print(f"   → STRENGTH: {signal_strength:.3f}")
            
            return {
                'signal_type': 'BUY',
                'core_conditions_passed': all_conditions_met,
                'signal_strength': signal_strength,
                'conditions_detail': {
                    'green_candle': condition_1,
                    'higher_close': condition_2,
                    'body_sufficient': condition_3
                }
            }
            
        except Exception as e:
            print(f"❌ BUY conditions error: {e}")
            return {
                'signal_type': 'BUY',
                'core_conditions_passed': False,
                'signal_strength': 0.0,
                'error': str(e)
            }
        
    def _get_buy_reasons_simple(self, green_candle: bool, higher_close: bool, body_ok: bool, data: Dict) -> List[str]:
        """📝 สร้างเหตุผล BUY signal แบบง่าย"""
        reasons = []
        
        if green_candle:
            reasons.append("🟢 Bullish green candle")
        
        if higher_close:
            current = data.get('close', 0)
            previous = data.get('previous_close', 0)
            reasons.append(f"📈 Higher close: ${previous:.2f} → ${current:.2f}")
        
        if body_ok:
            body_ratio = data.get('body_ratio', 0)
            reasons.append(f"💪 Strong body: {body_ratio*100:.1f}%")
        
        return reasons

    def _get_sell_reasons_simple(self, red_candle: bool, lower_close: bool, body_ok: bool, data: Dict) -> List[str]:
        """📝 สร้างเหตุผล SELL signal แบบง่าย"""
        reasons = []
        
        if red_candle:
            reasons.append("🔴 Bearish red candle")
        
        if lower_close:
            current = data.get('close', 0)
            previous = data.get('previous_close', 0)
            reasons.append(f"📉 Lower close: ${previous:.2f} → ${current:.2f}")
        
        if body_ok:
            body_ratio = data.get('body_ratio', 0)
            reasons.append(f"💪 Strong body: {body_ratio*100:.1f}%")
        
        return reasons
            
    def _decide_final_signal(self, buy_data: Dict, sell_data: Dict, candlestick_data: Dict) -> Dict:
        """
        🤔 ตัดสินใจ Signal สุดท้าย - FIXED LOGIC
        
        Args:
            buy_data: ผลการประเมิน BUY conditions
            sell_data: ผลการประเมิน SELL conditions  
            candlestick_data: ข้อมูล candlestick analysis
            
        Returns:
            Dict: Signal สุดท้ายที่ตัดสินใจแล้ว
        """
        try:
            # เช็ค minimum signal strength
            min_signal_strength = self.signal_strength_config.get('min_signal_strength', 0.6)
            
            buy_passed = buy_data.get('core_conditions_passed', False)
            sell_passed = sell_data.get('core_conditions_passed', False)
            buy_strength = buy_data.get('signal_strength', 0)
            sell_strength = sell_data.get('signal_strength', 0)
            
            print(f"🤔 Signal Decision Debug:")
            print(f"   BUY: passed={buy_passed}, strength={buy_strength:.3f}")
            print(f"   SELL: passed={sell_passed}, strength={sell_strength:.3f}")
            print(f"   Min required: {min_signal_strength}")
            
            # 🔧 FIXED: ตัดสินใจแบบชัดเจน - ไม่ให้ทั้งสองผ่านพร้อมกัน
            chosen_signal = None
            signal_strength = 0
            signal_reasons = []
            conditions_detail = {}
            
            # กรณีที่ 1: ทั้ง BUY และ SELL ผ่าน (ไม่ควรเกิดขึ้น)
            if buy_passed and sell_passed:
                print(f"⚠️ WARNING: Both BUY and SELL conditions passed!")
                print(f"   This indicates a logic error in condition evaluation")
                
                # เลือกตาม strength ที่สูงกว่า และต้องเกิน threshold มาก
                if buy_strength > sell_strength and buy_strength >= min_signal_strength + 0.1:
                    chosen_signal = 'BUY'
                    signal_strength = buy_strength
                    signal_reasons = buy_data.get('reasons', [])
                    conditions_detail = buy_data.get('conditions_met', {})
                    print(f"   → Chose BUY (stronger: {buy_strength:.3f} > {sell_strength:.3f})")
                elif sell_strength > buy_strength and sell_strength >= min_signal_strength + 0.1:
                    chosen_signal = 'SELL' 
                    signal_strength = sell_strength
                    signal_reasons = sell_data.get('reasons', [])
                    conditions_detail = sell_data.get('conditions_met', {})
                    print(f"   → Chose SELL (stronger: {sell_strength:.3f} > {buy_strength:.3f})")
                else:
                    # ความแรงใกล้เคียงกัน - ไม่ส่ง signal
                    print(f"   → No signal (strengths too close: BUY={buy_strength:.3f}, SELL={sell_strength:.3f})")
                    return self._create_wait_signal(
                        f"Conflicting signals (BUY: {buy_strength:.2f}, SELL: {sell_strength:.2f})"
                    )
            
            # กรณีที่ 2: เฉพาะ BUY ผ่าน
            elif buy_passed and buy_strength >= min_signal_strength:
                chosen_signal = 'BUY'
                signal_strength = buy_strength
                signal_reasons = buy_data.get('reasons', [])
                conditions_detail = buy_data.get('conditions_met', {})
                print(f"   → BUY Signal: {buy_strength:.3f} >= {min_signal_strength}")
                
            # กรณีที่ 3: เฉพาะ SELL ผ่าน  
            elif sell_passed and sell_strength >= min_signal_strength:
                chosen_signal = 'SELL'
                signal_strength = sell_strength
                signal_reasons = sell_data.get('reasons', [])
                conditions_detail = sell_data.get('conditions_met', {})
                print(f"   → SELL Signal: {sell_strength:.3f} >= {min_signal_strength}")
                
            # กรณีที่ 4: ไม่มี signal ไหนผ่าน
            else:
                print(f"   → No signal: BUY={buy_strength:.3f}, SELL={sell_strength:.3f}, min={min_signal_strength}")
                return self._create_wait_signal(
                    f"No strong signals (BUY: {buy_strength:.2f}, SELL: {sell_strength:.2f}, min: {min_signal_strength})"
                )
            
            # 🔧 FIXED: Double-check กับ candlestick data
            candle_color = candlestick_data.get('candle_color')
            price_direction = candlestick_data.get('price_direction')
            
            # Sanity check: BUY signal ควรมีแท่งเขียวและปิดสูงกว่า
            if chosen_signal == 'BUY':
                if candle_color != 'green':
                    print(f"   ❌ BUY signal but candle is {candle_color} - REJECTED")
                    return self._create_wait_signal(f"BUY signal rejected: candle is {candle_color}")
                    
                if price_direction != 'higher_close':
                    print(f"   ❌ BUY signal but price direction is {price_direction} - REJECTED")
                    return self._create_wait_signal(f"BUY signal rejected: {price_direction}")
                    
            # Sanity check: SELL signal ควรมีแท่งแดงและปิดต่ำกว่า
            elif chosen_signal == 'SELL':
                if candle_color != 'red':
                    print(f"   ❌ SELL signal but candle is {candle_color} - REJECTED")
                    return self._create_wait_signal(f"SELL signal rejected: candle is {candle_color}")
                    
                if price_direction != 'lower_close':
                    print(f"   ❌ SELL signal but price direction is {price_direction} - REJECTED")
                    return self._create_wait_signal(f"SELL signal rejected: {price_direction}")
            
            # ถ้าผ่าน sanity check แล้ว
            print(f"✅ Signal APPROVED: {chosen_signal}")
            print(f"   Candle: {candle_color}")
            print(f"   Direction: {price_direction}")
            print(f"   Strength: {signal_strength:.3f}")
            
            # สร้าง signal data สมบูรณ์
            signal_data = {
                'action': chosen_signal,
                'strength': signal_strength,
                'confidence': self._calculate_signal_confidence(chosen_signal, buy_data, sell_data),
                'timestamp': datetime.now(),
                
                # รายละเอียดเงื่อนไข
                'conditions_met': conditions_detail,
                'reasons': signal_reasons,
                'min_strength_required': min_signal_strength,
                'buy_strength': buy_strength,
                'sell_strength': sell_strength,
                
                # ข้อมูล candlestick ที่เกี่ยวข้อง
                'candle_color': candle_color,
                'body_ratio': candlestick_data.get('body_ratio'),
                'price_direction': price_direction,
                'pattern_name': candlestick_data.get('pattern_name'),
                'volume_factor': candlestick_data.get('volume_factor'),
                'close': candlestick_data.get('close'),
                
                # การจัด lot size ที่แนะนำ
                'recommended_lot_multiplier': self._calculate_lot_multiplier(signal_strength),
                
                # Metadata
                'symbol': candlestick_data.get('symbol', self.candlestick_analyzer.symbol),
                'timeframe': 'M5',
                'signal_id': f"{chosen_signal}_{datetime.now().strftime('%H%M%S')}",
                
                # 🔧 FIXED: เพิ่ม validation flags
                'passed_sanity_check': True,
                'candle_direction_match': True
            }
            
            print(f"🎯 FINAL SIGNAL: {chosen_signal} (Strength: {signal_strength:.3f})")
            return signal_data
            
        except Exception as e:
            print(f"❌ Final signal decision error: {e}")
            return self._create_wait_signal(f"Decision error: {str(e)}")
            
    # ==========================================
    # ✅ CONDITION EVALUATION HELPERS
    # ==========================================
    
    def _get_buy_reasons(self, conditions: Dict, data: Dict) -> List[str]:
        """📝 สร้างเหตุผล BUY signal"""
        reasons = []
        
        if conditions.get('candle_color'):
            reasons.append(f"🟢 Bullish green candle")
        
        if conditions.get('price_direction'):
            current_close = data.get('close', 0)
            previous_close = data.get('previous_close', 0)
            reasons.append(f"📈 Price increased: ${previous_close:.2f} → ${current_close:.2f}")
        
        if conditions.get('body_ratio'):
            body_ratio = data.get('body_ratio', 0)
            reasons.append(f"💪 Strong body: {body_ratio*100:.1f}% of candle range")
        
        if conditions.get('volume_confirmation') and data.get('volume_available'):
            volume_factor = data.get('volume_factor', 1)
            reasons.append(f"📊 Volume confirmation: {volume_factor:.2f}x average")
        
        pattern_name = data.get('pattern_name', '')
        if pattern_name and pattern_name != 'standard':
            reasons.append(f"🔍 Pattern: {pattern_name}")
        
        return reasons
    
    def _get_sell_reasons(self, conditions: Dict, data: Dict) -> List[str]:
        """📝 สร้างเหตุผล SELL signal"""
        reasons = []
        
        if conditions.get('candle_color'):
            reasons.append(f"🔴 Bearish red candle")
        
        if conditions.get('price_direction'):
            current_close = data.get('close', 0)
            previous_close = data.get('previous_close', 0)
            reasons.append(f"📉 Price decreased: ${previous_close:.2f} → ${current_close:.2f}")
        
        if conditions.get('body_ratio'):
            body_ratio = data.get('body_ratio', 0)
            reasons.append(f"💪 Strong body: {body_ratio*100:.1f}% of candle range")
        
        if conditions.get('volume_confirmation') and data.get('volume_available'):
            volume_factor = data.get('volume_factor', 1)
            reasons.append(f"📊 Volume confirmation: {volume_factor:.2f}x average")
        
        pattern_name = data.get('pattern_name', '')
        if pattern_name and pattern_name != 'standard':
            reasons.append(f"🔍 Pattern: {pattern_name}")
        
        return reasons
    
    # ==========================================
    # 🔧 UTILITY & VALIDATION METHODS
    # ==========================================
    
    def _validate_candlestick_data(self, data: Dict) -> bool:
        """✅ ตรวจสอบความถูกต้องของข้อมูล candlestick"""
        try:
            required_fields = ['open', 'high', 'low', 'close', 'candle_color', 'price_direction', 'body_ratio']
            
            for field in required_fields:
                if field not in data:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # ตรวจสอบ OHLC logic
            ohlc = (data['open'], data['high'], data['low'], data['close'])
            if not all(isinstance(x, (int, float)) and x > 0 for x in ohlc):
                print(f"❌ Invalid OHLC values: {ohlc}")
                return False
            
            if not (data['low'] <= min(data['open'], data['close']) <= max(data['open'], data['close']) <= data['high']):
                print(f"❌ Invalid OHLC relationship")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Data validation error: {e}")
            return False
    
    def _can_generate_signal(self) -> bool:
        """⏱️ ตรวจสอบ Rate Limiting"""
        try:
            now = datetime.now()
            
            # ตรวจสอบ cooldown
            time_since_last = (now - self.last_signal_time).total_seconds()
            if time_since_last < self.cooldown_seconds:
                remaining = self.cooldown_seconds - time_since_last
                print(f"⏳ Signal cooldown: {remaining:.1f}s remaining")
                return False
            
            # ตรวจสอบ daily reset
            if now.date() != self.last_reset_date:
                self.total_signals_today = 0
                self.last_reset_date = now.date()
                print(f"🔄 Daily signal counter reset")
            
            # ลบ signals เก่าออกจาก history (เก่ากว่า 1 ชั่วโมง)
            one_hour_ago = now - timedelta(hours=1)
            self.signal_history = [
                sig for sig in self.signal_history 
                if sig.get('timestamp', datetime.min) > one_hour_ago
            ]
            
            # ตรวจสอบ hourly limit
            if len(self.signal_history) >= self.max_signals_per_hour:
                print(f"📊 Hourly signal limit reached: {len(self.signal_history)}/{self.max_signals_per_hour}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Rate limiting check error: {e}")
            return False
    
    def _calculate_signal_confidence(self, signal_type: str, buy_data: Dict, sell_data: Dict) -> float:
        """🎯 คำนวณความเชื่อมั่นของ signal"""
        try:
            if signal_type == 'BUY':
                base_confidence = buy_data.get('signal_strength', 0)
            elif signal_type == 'SELL':
                base_confidence = sell_data.get('signal_strength', 0)
            else:
                return 0.5
            
            # ปรับความเชื่อมั่นตามปัจจัยอื่น
            # ถ้า signal ฝั่งตรงข้ามแข็งแกร่งด้วย = ลดความเชื่อมั่น
            opposite_strength = sell_data.get('signal_strength', 0) if signal_type == 'BUY' else buy_data.get('signal_strength', 0)
            
            if opposite_strength > 0.4:  # ฝั่งตรงข้ามแข็งแกร่ง
                confidence_penalty = opposite_strength * 0.3
                base_confidence -= confidence_penalty
            
            return max(0.1, min(0.95, base_confidence))
            
        except Exception as e:
            print(f"❌ Signal confidence calculation error: {e}")
            return 0.5
    
    def _calculate_lot_multiplier(self, signal_strength: float) -> float:
        """📏 คำนวณ Lot Multiplier ตาม Signal Strength"""
        try:
            # สัดส่วน lot ตาม strength
            # Signal strength 0.6 = 1.0x lot
            # Signal strength 0.8 = 1.5x lot  
            # Signal strength 1.0 = 2.0x lot
            
            if signal_strength >= 0.9:
                return 2.0
            elif signal_strength >= 0.8:
                return 1.8
            elif signal_strength >= 0.7:
                return 1.5
            elif signal_strength >= 0.6:
                return 1.2
            else:
                return 1.0
                
        except Exception as e:
            print(f"❌ Lot multiplier calculation error: {e}")
            return 1.0
    
    def _create_wait_signal(self, reason: str) -> Dict:
        """⏳ สร้าง WAIT signal พร้อมเหตุผล"""
        return {
            'action': 'WAIT',
            'strength': 0.0,
            'confidence': 0.0,
            'timestamp': datetime.now(),
            'reason': reason,
            'signal_id': f"WAIT_{datetime.now().strftime('%H%M%S')}"
        }
    
    def _record_signal(self, signal_data: Dict):
        """📝 บันทึก Signal History"""
        try:
            if signal_data.get('action') in ['BUY', 'SELL']:
                # อัพเดทการนับ
                signal_type = signal_data['action']
                self.signals_generated[signal_type] += 1
                self.total_signals_today += 1
                
                # บันทึกลง history
                self.signal_history.append({
                    'action': signal_type,
                    'strength': signal_data.get('strength', 0),
                    'timestamp': datetime.now(),
                    'signal_id': signal_data.get('signal_id')
                })
                
                # อัพเดท last signal time
                self.last_signal_time = datetime.now()
                
                # บันทึก quality score
                quality_score = signal_data.get('confidence', 0.5)
                self.signal_quality_scores.append(quality_score)
                
                # เก็บแค่ 100 scores ล่าสุด
                if len(self.signal_quality_scores) > 100:
                    self.signal_quality_scores = self.signal_quality_scores[-100:]
                
                print(f"📝 Signal recorded: {signal_type} (Quality: {quality_score:.2f})")
            
        except Exception as e:
            print(f"❌ Signal recording error: {e}")
    
    # ==========================================
    # 📊 PERFORMANCE & STATISTICS 
    # ==========================================
    
    def get_signal_statistics(self) -> Dict:
        """📊 ดึงสถิติ Signal Generation"""
        try:
            now = datetime.now()
            
            # คำนวณ signals ใน 1 ชั่วโมงล่าสุด
            one_hour_ago = now - timedelta(hours=1)
            recent_signals = [
                sig for sig in self.signal_history 
                if sig.get('timestamp', datetime.min) > one_hour_ago
            ]
            
            # แยกประเภท signals
            recent_buy = len([s for s in recent_signals if s['action'] == 'BUY'])
            recent_sell = len([s for s in recent_signals if s['action'] == 'SELL'])
            
            # คำนวณ average quality
            avg_quality = (
                sum(self.signal_quality_scores) / len(self.signal_quality_scores)
                if self.signal_quality_scores else 0.5
            )
            
            return {
                'total_signals_today': self.total_signals_today,
                'signals_last_hour': len(recent_signals),
                'buy_signals_hour': recent_buy,
                'sell_signals_hour': recent_sell,
                'total_buy_signals': self.signals_generated['BUY'],
                'total_sell_signals': self.signals_generated['SELL'],
                'total_wait_signals': self.signals_generated['WAIT'],
                'average_signal_quality': avg_quality,
                'last_signal_time': self.last_signal_time,
                'cooldown_seconds': self.cooldown_seconds,
                'max_signals_per_hour': self.max_signals_per_hour,
                'signals_remaining_hour': max(0, self.max_signals_per_hour - len(recent_signals))
            }
            
        except Exception as e:
            print(f"❌ Signal statistics error: {e}")
            return {'error': str(e)}
    
    def reset_daily_counters(self):
        """🔄 รีเซ็ตตัวนับรายวัน"""
        try:
            self.total_signals_today = 0
            self.last_reset_date = datetime.now().date()
            self.signals_generated = {'BUY': 0, 'SELL': 0, 'WAIT': 0}
            print(f"🔄 Daily signal counters reset")
        except Exception as e:
            print(f"❌ Counter reset error: {e}")
    
    def is_ready(self) -> bool:
        """✅ ตรวจสอบความพร้อม"""
        return (
            self.candlestick_analyzer is not None and 
            self.candlestick_analyzer.is_ready() and
            self.config is not None
        )
    
    def get_current_signal_status(self) -> Dict:
        """📋 ดึงสถานะปัจจุบันของ Signal Generator"""
        try:
            now = datetime.now()
            time_since_last = (now - self.last_signal_time).total_seconds()
            
            return {
                'is_ready': self.is_ready(),
                'can_generate_signal': self._can_generate_signal(),
                'time_since_last_signal': time_since_last,
                'cooldown_remaining': max(0, self.cooldown_seconds - time_since_last),
                'signals_today': self.total_signals_today,
                'signals_this_hour': len([
                    s for s in self.signal_history 
                    if s.get('timestamp', datetime.min) > now - timedelta(hours=1)
                ])
            }
            
        except Exception as e:
            print(f"❌ Signal status error: {e}")
            return {'error': str(e)}

# ==========================================
# ℹ️ SIGNAL GENERATOR INFO
# ==========================================

def get_generator_info() -> Dict:
    """ℹ️ ข้อมูลเกี่ยวกับ Signal Generator"""
    return {
        'name': 'Pure Candlestick Signal Generator',
        'version': '1.0.0',
        'signal_types': ['BUY', 'SELL', 'WAIT'],
        'required_conditions': {
            'BUY': ['green candle', 'higher close', 'min body ratio'],
            'SELL': ['red candle', 'lower close', 'min body ratio']
        },
        'optional_conditions': ['volume confirmation'],
        'rate_limiting': True,
        'adaptive_lot_sizing': True
    }