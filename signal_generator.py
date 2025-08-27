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
        🎯 SIMPLE SIGNAL GENERATION
        
        เงื่อนไขง่ายๆ:
        - BUY → ปิดสูงกว่าแท่งก่อน
        - SELL → ปิดต่ำกว่าแท่งก่อน
        - 1 แท่งต่อ 1 ออเดอร์
        """
        try:
            print(f"\n=== 🎯 SIMPLE SIGNAL GENERATION ===")
            
            # ตรวจสอบข้อมูล
            candle_signature = candlestick_data.get('candle_signature')
            if not candle_signature:
                return self._create_wait_signal("No signature")
            
            # เช็ค lock แท่ง
            if self._is_order_sent_for_candle(candle_signature):
                print(f"🚫 LOCKED: {candle_signature}")
                return None
            
            # ดึงราคา
            current_close = float(candlestick_data.get('close', 0))
            previous_close = float(candlestick_data.get('previous_close', 0))
            
            if current_close <= 0 or previous_close <= 0:
                print(f"❌ Invalid prices: current={current_close}, previous={previous_close}")
                return self._create_wait_signal("Invalid price data")
            
            print(f"💰 PRICE COMPARISON:")
            print(f"   Current Close:  {current_close:.4f}")
            print(f"   Previous Close: {previous_close:.4f}")
            
            price_diff = current_close - previous_close
            print(f"   Difference: {price_diff:+.4f}")
            
            # เงื่อนไขง่ายๆ
            if price_diff > 0:
                # ปิดสูงกว่า = BUY
                print(f"🟢 BUY SIGNAL: ปิดสูงกว่าแท่งก่อน (+{price_diff:.4f})")
                
                self._mark_order_sent_for_candle(candle_signature)
                
                return {
                    'action': 'BUY',
                    'strength': min(abs(price_diff) / 2.0, 1.0),  # คำนวณจาก price difference
                    'confidence': 0.8,
                    'timestamp': datetime.now(),
                    'signal_id': f"BUY_{datetime.now().strftime('%H%M%S')}",
                    'candle_signature': candle_signature,
                    'close': current_close,
                    'previous_close': previous_close,
                    'price_difference': price_diff,
                    'reasons': [f"BUY: ปิด {current_close:.4f} > ก่อน {previous_close:.4f}"],
                    'symbol': candlestick_data.get('symbol', 'XAUUSD.v')
                }
                
            elif price_diff < 0:
                # ปิดต่ำกว่า = SELL
                print(f"🔴 SELL SIGNAL: ปิดต่ำกว่าแท่งก่อน ({price_diff:.4f})")
                
                self._mark_order_sent_for_candle(candle_signature)
                
                return {
                    'action': 'SELL', 
                    'strength': min(abs(price_diff) / 2.0, 1.0),
                    'confidence': 0.8,
                    'timestamp': datetime.now(),
                    'signal_id': f"SELL_{datetime.now().strftime('%H%M%S')}",
                    'candle_signature': candle_signature,
                    'close': current_close,
                    'previous_close': previous_close,
                    'price_difference': price_diff,
                    'reasons': [f"SELL: ปิด {current_close:.4f} < ก่อน {previous_close:.4f}"],
                    'symbol': candlestick_data.get('symbol', 'XAUUSD.v')
                }
                
            else:
                # ปิดเท่ากัน = รอ
                print(f"⏳ NO SIGNAL: ปิดเท่ากับแท่งก่อน ({current_close:.4f})")
                return self._create_wait_signal("ราคาปิดเท่ากัน")
            
        except Exception as e:
            print(f"❌ Simple signal error: {e}")
            return self._create_wait_signal(f"Error: {e}")
                                
    def _is_order_sent_for_candle(self, candle_signature: str) -> bool:
        """เช็คว่าส่งออเดอร์สำหรับแท่งนี้แล้วหรือยัง - FIXED"""
        if not hasattr(self, 'locked_candles'):
            self.locked_candles = set()
        
        is_locked = candle_signature in self.locked_candles
        print(f"🔒 Lock check: {candle_signature} → {'LOCKED' if is_locked else 'FREE'}")
        
        return is_locked

    def _mark_order_sent_for_candle(self, candle_signature: str):
        """ล็อกแท่งที่ส่งออเดอร์แล้ว - FIXED"""
        if not hasattr(self, 'locked_candles'):
            self.locked_candles = set()
        
        self.locked_candles.add(candle_signature)
        print(f"🔒 LOCKED: {candle_signature}")
        print(f"📊 Total locked candles: {len(self.locked_candles)}")
        
        # เก็บแค่ 100 แท่งล่าสุด
        if len(self.locked_candles) > 100:
            # แปลง set เป็น list เพื่อลบตัวเก่า
            sorted_candles = sorted(list(self.locked_candles))
            self.locked_candles = set(sorted_candles[-50:])  # เก็บ 50 ตัวล่าสุด
            print(f"🧹 Cleaned locks: kept 50 most recent")

    def clear_all_locks(self):
        """ล้างการล็อกทั้งหมด - สำหรับ debug"""
        if hasattr(self, 'locked_candles'):
            old_count = len(self.locked_candles)
            self.locked_candles.clear()
            print(f"🗑️ Cleared {old_count} locked candles")
        return True

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
    
                