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
        🎯 FINAL CORRECT SIGNAL GENERATION
        
        เงื่อนไข:
        - BUY → if Close[1] > High[2] 
        - SELL → if Close[1] < Low[2]
        """
        try:
            print(f"\n=== 🎯 SIGNAL: Close[1] vs High[2]/Low[2] ===")
            
            # ตรวจสอบข้อมูล
            candle_signature = candlestick_data.get('candle_signature')
            if not candle_signature:
                return self._create_wait_signal("No signature")
            
            # เช็ค lock
            if self._is_order_sent_for_candle(candle_signature):
                print(f"🚫 LOCKED: {candle_signature}")
                return None
            
            # ดึงข้อมูลที่ถูกต้อง
            close_1 = float(candlestick_data.get('close', 0))        # Close[1]
            high_2 = float(candlestick_data.get('previous_high', 0)) # High[2]
            low_2 = float(candlestick_data.get('previous_low', 0))   # Low[2]
            
            print(f"📊 DATA:")
            print(f"   Close[1]: {close_1:.4f}")
            print(f"   High[2]:  {high_2:.4f}")
            print(f"   Low[2]:   {low_2:.4f}")
            
            # เงื่อนไข BUY: Close[1] > High[2]
            if close_1 > high_2:
                breakout = close_1 - high_2
                
                print(f"🟢 BUY SIGNAL!")
                print(f"   Close[1] {close_1:.4f} > High[2] {high_2:.4f}")
                print(f"   Breakout: +{breakout:.4f}")
                
                self._mark_order_sent_for_candle(candle_signature)
                
                return {
                    'action': 'BUY',
                    'strength': min(breakout * 2.0, 1.0),
                    'confidence': 0.9,
                    'timestamp': datetime.now(),
                    'signal_id': f"BUY_{datetime.now().strftime('%H%M%S')}",
                    'candle_signature': candle_signature,
                    'close': close_1,
                    'reference_high': high_2,
                    'breakout_amount': breakout,
                    'reasons': [f"BUY: Close[1] {close_1:.4f} > High[2] {high_2:.4f}"],
                    'symbol': candlestick_data.get('symbol', 'XAUUSD.v')
                }
            
            # เงื่อนไข SELL: Close[1] < Low[2]
            elif close_1 < low_2:
                breakdown = low_2 - close_1
                
                print(f"🔴 SELL SIGNAL!")
                print(f"   Close[1] {close_1:.4f} < Low[2] {low_2:.4f}")
                print(f"   Breakdown: -{breakdown:.4f}")
                
                self._mark_order_sent_for_candle(candle_signature)
                
                return {
                    'action': 'SELL',
                    'strength': min(breakdown * 2.0, 1.0),
                    'confidence': 0.9,
                    'timestamp': datetime.now(),
                    'signal_id': f"SELL_{datetime.now().strftime('%H%M%S')}",
                    'candle_signature': candle_signature,
                    'close': close_1,
                    'reference_low': low_2,
                    'breakdown_amount': breakdown,
                    'reasons': [f"SELL: Close[1] {close_1:.4f} < Low[2] {low_2:.4f}"],
                    'symbol': candlestick_data.get('symbol', 'XAUUSD.v')
                }
            
            # ไม่ตรงเงื่อนไข
            else:
                print(f"⏳ NO SIGNAL: Low[2] {low_2:.4f} <= Close[1] {close_1:.4f} <= High[2] {high_2:.4f}")
                return self._create_wait_signal("ไม่มี breakout/breakdown")
            
        except Exception as e:
            print(f"❌ Signal error: {e}")
            return self._create_wait_signal(f"Error: {e}")
                            
    def _is_order_sent_for_candle(self, candle_signature: str) -> bool:
        """เช็คว่าส่งออเดอร์สำหรับแท่งนี้แล้วหรือยัง"""
        if not hasattr(self, 'locked_candles'):
            self.locked_candles = set()
        return candle_signature in self.locked_candles

    def _mark_order_sent_for_candle(self, candle_signature: str):
        """ล็อกแท่งที่ส่งออเดอร์แล้ว"""
        if not hasattr(self, 'locked_candles'):
            self.locked_candles = set()
        
        self.locked_candles.add(candle_signature)
        print(f"🔒 LOCKED: {candle_signature}")
        
        # เก็บแค่ 50 แท่งล่าสุด
        if len(self.locked_candles) > 50:
            oldest = next(iter(self.locked_candles))
            self.locked_candles.remove(oldest)

    def _record_signal(self, signal_data: Dict):
        """บันทึก Signal"""
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

    def _create_wait_signal(self, reason: str) -> Dict:
        """สร้าง WAIT signal"""
        return {
            'action': 'WAIT',
            'strength': 0.0,
            'confidence': 0.0,
            'timestamp': datetime.now(),
            'reason': reason,
            'signal_id': f"WAIT_{datetime.now().strftime('%H%M%S')}"
        }

    def _record_signal(self, signal_data: Dict):
        """บันทึก Signal History"""
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
                
            print(f"Signal recorded: {action}")
            
        except Exception as e:
            print(f"Record signal error: {e}")

    def _validate_candlestick_data(self, data: Dict) -> bool:
        """✅ ตรวจสอบความถูกต้องของข้อมูล candlestick - สำหรับการปิดคุม"""
        try:
            required_fields = ['close', 'previous_close', 'body_ratio']
            
            for field in required_fields:
                if field not in data:
                    print(f"❌ Missing required field: {field}")
                    return False
                    
            # ตรวจสอบว่าเป็นตัวเลข
            close = data.get('close', 0)
            prev_close = data.get('previous_close', 0)
            body_ratio = data.get('body_ratio', 0)
            
            if not all(isinstance(x, (int, float)) and x > 0 for x in [close, prev_close]):
                print(f"❌ Invalid price values: close={close}, prev_close={prev_close}")
                return False
                
            if not (0 <= body_ratio <= 1):
                print(f"❌ Invalid body_ratio: {body_ratio}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Data validation error: {e}")
            return False

    def _can_generate_signal(self) -> bool:
        """
        🔧 SIMPLIFIED: ลดการตรวจสอบ rate limiting (เพราะใช้ timestamp แล้ว)
        """
        try:
            # เช็คแค่ว่าไม่ได้ส่ง signal บ่อยเกิน 1 ครั้งต่อ 5 วินาที
            now = datetime.now()
            time_since_last = (now - self.last_signal_time).total_seconds()
            
            if time_since_last < 5:  # อย่างน้อย 5 วินาทีระหว่าง signal
                print(f"⏳ Global cooldown: {5 - time_since_last:.1f}s remaining")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Rate limiting error: {e}")
            return True            

    def _mark_signal_sent_for_signature(self, signature: str):
        """
        ✅ บันทึกว่าส่ง signal สำหรับลายเซ็นนี้แล้ว
        (method ที่ data_persistence.py ต้องการ)
        """
        try:
            if not hasattr(self, 'signal_signatures'):
                self.signal_signatures = set()
                
            self.signal_signatures.add(signature)
            print(f"✅ Signal signature recorded: {signature}")
            
        except Exception as e:
            print(f"❌ Mark signal signature error: {e}")

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
    
                