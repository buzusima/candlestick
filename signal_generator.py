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
        🎯 สร้าง Signal - CLEAN VERSION (ไม่มี min_signal_strength)
        
        เงื่อนไขง่ายๆ:
        - BUY: ราคาปิดสูงกว่าแท่งก่อน + body แข็งแกร่ง
        - SELL: ราคาปิดต่ำกว่าแท่งก่อน + body แข็งแกร่ง
        """
        try:
            print(f"\n=== 🎯 SIGNAL GENERATION (CLEAN) ===")
            
            # ตรวจสอบ rate limiting
            if not self._can_generate_signal():
                return self._create_wait_signal("Rate limited")
            
            # ดึงข้อมูลราคา
            current_close = float(candlestick_data.get('close', 0))
            previous_close = float(candlestick_data.get('previous_close', 0))
            body_ratio = float(candlestick_data.get('body_ratio', 0))
            
            print(f"📊 ข้อมูล:")
            print(f"   ปิดปัจจุบัน: {current_close:.2f}")
            print(f"   ปิดแท่งก่อน: {previous_close:.2f}")
            print(f"   ต่างกัน: {current_close - previous_close:+.2f}")
            print(f"   Body: {body_ratio:.3f}")
            
            # เงื่อนไขง่ายๆ
            min_body = 0.1  # 10%
            
            # BUY: ปิดสูงกว่า + body พอ
            if current_close > previous_close and body_ratio >= min_body:
                signal_strength = min(abs(current_close - previous_close) / 3.0, 1.0)
                
                signal_data = {
                    'action': 'BUY',
                    'strength': signal_strength,
                    'confidence': signal_strength,
                    'timestamp': datetime.now(),
                    'signal_id': f"BUY_{datetime.now().strftime('%H%M%S')}",
                    'close': current_close,
                    'previous_close': previous_close,
                    'body_ratio': body_ratio,
                    'price_change': current_close - previous_close,
                    'reasons': [f"📈 ปิดสูงกว่า +{current_close - previous_close:.2f}"],
                    'symbol': candlestick_data.get('symbol', 'XAUUSD.v')
                }
                
                print(f"✅ BUY SIGNAL: ปิดคุมขาขึ้น (Strength: {signal_strength:.3f})")
                self._record_signal(signal_data)
                return signal_data
            
            # SELL: ปิดต่ำกว่า + body พอ
            elif current_close < previous_close and body_ratio >= min_body:
                signal_strength = min(abs(previous_close - current_close) / 3.0, 1.0)
                
                signal_data = {
                    'action': 'SELL',
                    'strength': signal_strength,
                    'confidence': signal_strength,
                    'timestamp': datetime.now(),
                    'signal_id': f"SELL_{datetime.now().strftime('%H%M%S')}",
                    'close': current_close,
                    'previous_close': previous_close,
                    'body_ratio': body_ratio,
                    'price_change': current_close - previous_close,
                    'reasons': [f"📉 ปิดต่ำกว่า {current_close - previous_close:.2f}"],
                    'symbol': candlestick_data.get('symbol', 'XAUUSD.v')
                }
                
                print(f"✅ SELL SIGNAL: ปิดคุมขาลง (Strength: {signal_strength:.3f})")
                self._record_signal(signal_data)
                return signal_data
            
            # ไม่ตรงเงื่อนไข
            else:
                print(f"⏳ WAIT: เงื่อนไขไม่ครบ")
                return self._create_wait_signal("เงื่อนไขไม่ครบ")
            
        except Exception as e:
            print(f"❌ Signal error: {e}")
            return self._create_wait_signal(f"Error: {e}")

    def _mark_signal_sent_for_signature(self, signature: str):
        """
        ✅ บันทึกว่าส่ง signal สำหรับลายเซ็นนี้แล้ว
        (method ที่ data_persistence.py ต้องการ)
        """
        try:
            self.signal_signatures.add(signature)
            print(f"✅ Signal signature recorded: {signature}")
        except Exception as e:
            print(f"❌ Mark signal signature error: {e}")
    
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
        """⏱️ ตรวจสอบ Rate Limiting - การปิดคุมเป็นหลัก"""
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
            
            print(f"✅ สามารถส่ง signal ได้ (signals this hour: {len(self.signal_history)}/{self.max_signals_per_hour})")
            return True
            
        except Exception as e:
            print(f"❌ Rate limiting check error: {e}")
            return False
                                    
            
                
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
    
