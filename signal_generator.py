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
        Lock เข้มงวด - ป้องกันส่งซ้ำ 100%
        """
        try:
            if not candlestick_data:
                return self._create_wait_signal("No data")
            
            # ดึง timestamp จากข้อมูล
            candle_timestamp = candlestick_data.get('candle_timestamp')
            if not candle_timestamp:
                return self._create_wait_signal("No timestamp")
            
            # เช็ค signal lock เข้มงวด
            if not hasattr(self, 'sent_signal_timestamps'):
                self.sent_signal_timestamps = set()
            
            if candle_timestamp in self.sent_signal_timestamps:
                print(f"SIGNAL BLOCKED - timestamp {candle_timestamp} already sent")
                return None
            
            # ดึงข้อมูลการ breakout/breakdown
            is_breakout = candlestick_data.get('breakout_detected', False)
            is_breakdown = candlestick_data.get('breakdown_detected', False)
            
            if not (is_breakout or is_breakdown):
                return self._create_wait_signal("No breakout/breakdown")
            
            # Lock timestamp นี้ทันที
            self.sent_signal_timestamps.add(candle_timestamp)
            print(f"SIGNAL TIMESTAMP LOCKED: {candle_timestamp}")
            
            # เก็บแค่ 20 timestamps
            if len(self.sent_signal_timestamps) > 20:
                timestamps_list = sorted(list(self.sent_signal_timestamps))
                self.sent_signal_timestamps = set(timestamps_list[-10:])
            
            if is_breakout:
                action = 'BUY'
                amount = candlestick_data.get('breakout_amount', 0)
            else:
                action = 'SELL'
                amount = candlestick_data.get('breakdown_amount', 0)
            
            print(f"SIGNAL CONFIRMED: {action} for timestamp {candle_timestamp}")
            
            return {
                'action': action,
                'strength': min(0.7 + (amount / 10.0), 1.0),
                'confidence': 0.9,
                'timestamp': datetime.now(),
                'signal_id': f"{action}_{candle_timestamp}",
                'candle_signature': f"SIGNAL_{candle_timestamp}",
                'candle_timestamp': candle_timestamp,
                'close': candlestick_data.get('close'),
                'amount': amount,
                'symbol': candlestick_data.get('symbol', 'XAUUSD.v')
            }
            
        except Exception as e:
            print(f"Signal error: {e}")
            return self._create_wait_signal(f"Error: {e}")
            
    def _is_signal_sent_for_signature(self, signature: str) -> bool:
        """🔒 เช็คว่าส่ง signal สำหรับแท่งนี้แล้วหรือยัง"""
        try:
            if not hasattr(self, 'signal_signatures'):
                self.signal_signatures = set()
            
            is_sent = signature in self.signal_signatures
            print(f"🔍 Signal check: {signature} → {'SENT' if is_sent else 'NEW'}")
            
            return is_sent
            
        except Exception as e:
            print(f"❌ Signal signature check error: {e}")
            return False

    def _mark_signal_sent_for_signature(self, signature: str):
        """🔒 บันทึกว่าส่ง signal สำหรับแท่งนี้แล้ว"""
        try:
            if not hasattr(self, 'signal_signatures'):
                self.signal_signatures = set()
            
            self.signal_signatures.add(signature)
            
            # เก็บแค่ 100 signatures ล่าสุด (ป้องกัน memory leak)
            if len(self.signal_signatures) > 100:
                signatures_list = list(self.signal_signatures)
                self.signal_signatures = set(signatures_list[-50:])
                print(f"🧹 Cleaned signal signatures: kept 50 recent")
            
            print(f"🔒 SIGNAL SIGNATURE LOCKED: {signature}")
            print(f"📊 Total locked signatures: {len(self.signal_signatures)}")
            
        except Exception as e:
            print(f"❌ Mark signal signature error: {e}")

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

    def clear_signal_locks(self):
        """🗑️ ล้างการล็อก signal ทั้งหมด (สำหรับ debug)"""
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
        """📊 ข้อมูลการล็อก signal"""
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
    
                