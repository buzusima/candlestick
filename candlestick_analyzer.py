"""
🎯 Pure Candlestick Signal Generator
signal_generator.py

🚀 Features:
✅ สร้าง BUY/SELL signals ตามกรัล Pure Candlestick
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
        
        print(f"🎯 Signal Generator initialized")
        print(f"   Cooldown: {self.cooldown_seconds}s between signals")
        print(f"   Max signals/hour: {self.max_signals_per_hour}")
        print(f"   Min body ratio: {self.buy_conditions.get('min_body_ratio', 0.1)*100:.1f}%")
    
    # ==========================================
    # 🎯 MAIN SIGNAL GENERATION
    # ==========================================
    
    def generate_signal(self, candlestick_data: Dict) -> Optional[Dict]:
        """
        🎯 สร้าง Trading Signal จากข้อมูล Candlestick
        
        Args:
            candlestick_data: ผลการวิเคราะห์จาก CandlestickAnalyzer
            
        Returns:
            Dict: Signal data หรือ None ถ้าไม่มี signal
        """
        try:
            # ตรวจสอบ rate limiting
            if not self._can_generate_signal():
                return self._create_wait_signal("Rate limited or in cooldown")
            
            # ตรวจสอบคุณภาพข้อมูล
            if not self._validate_candlestick_data(candlestick_data):
                return self._create_wait_signal("Invalid candlestick data")
            
            # วิเคราะห์เงื่อนไข BUY
            buy_signal_data = self._evaluate_buy_conditions(candlestick_data)
            
            # วิเคราะห์เงื่อนไข SELL
            sell_signal_data = self._evaluate_sell_conditions(candlestick_data)
            
            # ตัดสินใจ signal สุดท้าย
            final_signal = self._decide_final_signal(buy_signal_data, sell_signal_data, candlestick_data)
            
            # บันทึก signal history
            self._record_signal(final_signal)
            
            return final_signal
            
        except Exception as e:
            print(f"❌ Signal generation error: {e}")
            return self._create_wait_signal(f"Error: {str(e)}")
    
    def _evaluate_buy_conditions(self, data: Dict) -> Dict:
        """
        🟢 ประเมินเงื่อนไข BUY Signal
        
        Args:
            data: ข้อมูล candlestick analysis
            
        Returns:
            Dict: ผลการประเมิน BUY conditions
        """
        try:
            conditions_met = {}
            total_score = 0.0
            max_score = 0.0
            
            # 1. เช็ค Candle Color (Green)
            color_weight = self.signal_strength_config.get('candle_color_weight', 0.3)
            max_score += color_weight
            
            if data.get('candle_color') == 'green':
                conditions_met['candle_color'] = True
                total_score += color_weight
                print(f"✅ BUY: Green candle (+{color_weight})")
            else:
                conditions_met['candle_color'] = False
                print(f"❌ BUY: Not green candle")
            
            # 2. เช็ค Price Direction (Higher Close)
            direction_weight = self.signal_strength_config.get('price_direction_weight', 0.3)
            max_score += direction_weight
            
            if data.get('price_direction') == 'higher_close':
                conditions_met['price_direction'] = True
                total_score += direction_weight
                print(f"✅ BUY: Higher close (+{direction_weight})")
            else:
                conditions_met['price_direction'] = False
                print(f"❌ BUY: Not higher close")
            
            # 3. เช็ค Body Ratio
            body_weight = self.signal_strength_config.get('body_ratio_weight', 0.4)
            max_score += body_weight
            
            body_ratio = data.get('body_ratio', 0)
            min_body_ratio = self.buy_conditions.get('min_body_ratio', 0.1)
            
            if body_ratio >= min_body_ratio:
                conditions_met['body_ratio'] = True
                # คะแนนขึ้นอยู่กับขนาด body
                body_score = min(body_ratio * 2, 1.0) * body_weight  # แปลงเป็น 0-1
                total_score += body_score
                print(f"✅ BUY: Body ratio {body_ratio:.3f} >= {min_body_ratio} (+{body_score:.3f})")
            else:
                conditions_met['body_ratio'] = False
                print(f"❌ BUY: Body ratio {body_ratio:.3f} < {min_body_ratio}")
            
            # 4. เช็ค Volume Confirmation (Optional)
            volume_confirmation_required = self.buy_conditions.get('volume_confirmation', False)
            volume_threshold = self.buy_conditions.get('volume_factor_threshold', 1.2)
            
            if volume_confirmation_required:
                volume_factor = data.get('volume_factor', 1.0)
                
                if volume_factor >= volume_threshold:
                    conditions_met['volume_confirmation'] = True
                    print(f"✅ BUY: Volume confirmation {volume_factor:.2f} >= {volume_threshold}")
                else:
                    conditions_met['volume_confirmation'] = False
                    print(f"❌ BUY: Volume confirmation {volume_factor:.2f} < {volume_threshold}")
            else:
                conditions_met['volume_confirmation'] = True  # ไม่บังคับ
                print(f"ℹ️ BUY: Volume confirmation not required")
            
            # คำนวณ signal strength
            signal_strength = total_score / max_score if max_score > 0 else 0
            
            # ตรวจสอบว่าเงื่อนไขหลักผ่านหรือไม่
            core_conditions_met = (
                conditions_met.get('candle_color', False) and
                conditions_met.get('price_direction', False) and  
                conditions_met.get('body_ratio', False) and
                conditions_met.get('volume_confirmation', True)  # True ถ้าไม่บังคับ
            )
            
            return {
                'signal_type': 'BUY',
                'conditions_met': conditions_met,
                'core_conditions_passed': core_conditions_met,
                'signal_strength': signal_strength,
                'total_score': total_score,
                'max_score': max_score,
                'reasons': self._get_buy_reasons(conditions_met, data)
            }
            
        except Exception as e:
            print(f"❌ BUY conditions evaluation error: {e}")
            return {
                'signal_type': 'BUY',
                'core_conditions_passed': False,
                'signal_strength': 0.0,
                'error': str(e)
            }
    
    def _evaluate_sell_conditions(self, data: Dict) -> Dict:
        """
        🔴 ประเมินเงื่อนไข SELL Signal
        
        Args:
            data: ข้อมูล candlestick analysis
            
        Returns:
            Dict: ผลการประเมิน SELL conditions
        """
        try:
            conditions_met = {}
            total_score = 0.0
            max_score = 0.0
            
            # 1. เช็ค Candle Color (Red)
            color_weight = self.signal_strength_config.get('candle_color_weight', 0.3)
            max_score += color_weight
            
            if data.get('candle_color') == 'red':
                conditions_met['candle_color'] = True
                total_score += color_weight
                print(f"✅ SELL: Red candle (+{color_weight})")
            else:
                conditions_met['candle_color'] = False
                print(f"❌ SELL: Not red candle")
            
            # 2. เช็ค Price Direction (Lower Close)
            direction_weight = self.signal_strength_config.get('price_direction_weight', 0.3)
            max_score += direction_weight
            
            if data.get('price_direction') == 'lower_close':
                conditions_met['price_direction'] = True
                total_score += direction_weight
                print(f"✅ SELL: Lower close (+{direction_weight})")
            else:
                conditions_met['price_direction'] = False
                print(f"❌ SELL: Not lower close")
            
            # 3. เช็ค Body Ratio
            body_weight = self.signal_strength_config.get('body_ratio_weight', 0.4)
            max_score += body_weight
            
            body_ratio = data.get('body_ratio', 0)
            min_body_ratio = self.sell_conditions.get('min_body_ratio', 0.1)
            
            if body_ratio >= min_body_ratio:
                conditions_met['body_ratio'] = True
                # คะแนนขึ้นอยู่กับขนาด body
                body_score = min(body_ratio * 2, 1.0) * body_weight
                total_score += body_score
                print(f"✅ SELL: Body ratio {body_ratio:.3f} >= {min_body_ratio} (+{body_score:.3f})")
            else:
                conditions_met['body_ratio'] = False
                print(f"❌ SELL: Body ratio {body_ratio:.3f} < {min_body_ratio}")
            
            # 4. เช็ค Volume Confirmation (Optional)
            volume_confirmation_required = self.sell_conditions.get('volume_confirmation', False)
            volume_threshold = self.sell_conditions.get('volume_factor_threshold', 1.2)
            
            if volume_confirmation_required:
                volume_factor = data.get('volume_factor', 1.0)
                
                if volume_factor >= volume_threshold:
                    conditions_met['volume_confirmation'] = True
                    print(f"✅ SELL: Volume confirmation {volume_factor:.2f} >= {volume_threshold}")
                else:
                    conditions_met['volume_confirmation'] = False
                    print(f"❌ SELL: Volume confirmation {volume_factor:.2f} < {volume_threshold}")
            else:
                conditions_met['volume_confirmation'] = True  # ไม่บังคับ
                print(f"ℹ️ SELL: Volume confirmation not required")
            
            # คำนวณ signal strength
            signal_strength = total_score / max_score if max_score > 0 else 0
            
            # ตรวจสอบว่าเงื่อนไขหลักผ่านหรือไม่
            core_conditions_met = (
                conditions_met.get('candle_color', False) and
                conditions_met.get('price_direction', False) and
                conditions_met.get('body_ratio', False) and
                conditions_met.get('volume_confirmation', True)  # True ถ้าไม่บังคับ
            )
            
            return {
                'signal_type': 'SELL',
                'conditions_met': conditions_met,
                'core_conditions_passed': core_conditions_met,
                'signal_strength': signal_strength,
                'total_score': total_score,
                'max_score': max_score,
                'reasons': self._get_sell_reasons(conditions_met, data)
            }
            
        except Exception as e:
            print(f"❌ SELL conditions evaluation error: {e}")
            return {
                'signal_type': 'SELL',
                'core_conditions_passed': False,
                'signal_strength': 0.0,
                'error': str(e)
            }
    
    def _decide_final_signal(self, buy_data: Dict, sell_data: Dict, candlestick_data: Dict) -> Dict:
        """
        🤔 ตัดสินใจ Signal สุดท้าย
        
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
            
            # ตัดสินใจ signal
            if buy_passed and buy_strength >= min_signal_strength:
                if sell_passed and sell_strength > buy_strength:
                    # SELL แข็งแกร่งกว่า
                    chosen_signal = 'SELL'
                    signal_strength = sell_strength
                    signal_reasons = sell_data.get('reasons', [])
                    conditions_detail = sell_data.get('conditions_met', {})
                else:
                    # BUY
                    chosen_signal = 'BUY'
                    signal_strength = buy_strength
                    signal_reasons = buy_data.get('reasons', [])
                    conditions_detail = buy_data.get('conditions_met', {})
                    
            elif sell_passed and sell_strength >= min_signal_strength:
                # SELL
                chosen_signal = 'SELL'
                signal_strength = sell_strength
                signal_reasons = sell_data.get('reasons', [])
                conditions_detail = sell_data.get('conditions_met', {})
                
            else:
                # ไม่มี signal
                return self._create_wait_signal(
                    f"No strong signals (BUY: {buy_strength:.2f}, SELL: {sell_strength:.2f}, min: {min_signal_strength})"
                )
            
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
                'candle_color': candlestick_data.get('candle_color'),
                'body_ratio': candlestick_data.get('body_ratio'),
                'price_direction': candlestick_data.get('price_direction'),
                'pattern_name': candlestick_data.get('pattern_name'),
                'volume_factor': candlestick_data.get('volume_factor'),
                
                # การจัด lot size ที่แนะนำ
                'recommended_lot_multiplier': self._calculate_lot_multiplier(signal_strength),
                
                # Metadata
                'symbol': candlestick_data.get('symbol', self.candlestick_analyzer.symbol),
                'timeframe': 'M5',
                'signal_id': f"{chosen_signal}_{datetime.now().strftime('%H%M%S')}"
            }
            
            print(f"🎯 SIGNAL GENERATED: {chosen_signal} (Strength: {signal_strength:.2f})")
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