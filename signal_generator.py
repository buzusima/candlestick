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
        เงื่อนไขที่ถูกต้อง:
        BUY: Close[1] > Close[2] AND Close[1] > Open[1]
        SELL: Close[1] < Close[2] AND Close[1] < Open[1]
        """
        try:
            print(f"\n=== CORRECT SIGNAL CONDITIONS ===")
            
            # ตรวจสอบ rate limiting
            if not self._can_generate_signal():
                return self._create_wait_signal("Rate limited")
            
            # ดึงข้อมูล
            close_1 = float(candlestick_data.get('close', 0))         # Close[1] - แท่งปิดล่าสุด
            open_1 = float(candlestick_data.get('open', 0))           # Open[1] - แท่งปิดล่าสุด
            close_2 = float(candlestick_data.get('previous_close', 0)) # Close[2] - แท่งก่อนหน้า
            body_ratio = float(candlestick_data.get('body_ratio', 0))
            
            print(f"แท่ง 1: Open={open_1:.2f}, Close={close_1:.2f}")
            print(f"แท่ง 2: Close={close_2:.2f}")
            
            # เงื่อนไขพื้นฐาน
            min_body_ratio = 0.01
            min_price_diff = 0.05
            
            if body_ratio < min_body_ratio:
                return self._create_wait_signal(f"Body ต่ำ: {body_ratio:.3f}")
            
            # ตรวจสอบเงื่อนไข BUY
            condition_close_higher = close_1 > close_2  # Close[1] > Close[2]
            condition_green_candle = close_1 > open_1   # Close[1] > Open[1] (แท่งเขียว)
            price_diff_1_2 = close_1 - close_2
            
            print(f"BUY Conditions:")
            print(f"  Close[1] > Close[2]: {close_1:.2f} > {close_2:.2f} = {condition_close_higher}")
            print(f"  Close[1] > Open[1]: {close_1:.2f} > {open_1:.2f} = {condition_green_candle}")
            print(f"  Price diff: {price_diff_1_2:+.2f}")
            
            if condition_close_higher and condition_green_candle and abs(price_diff_1_2) >= min_price_diff:
                signal_strength = min(abs(price_diff_1_2) / 2.0, 1.0)
                
                print(f"✅ BUY SIGNAL: แท่งเขียวปิดสูงกว่าแท่งก่อน")
                
                signal_data = {
                    'action': 'BUY',
                    'strength': signal_strength,
                    'confidence': signal_strength,
                    'timestamp': datetime.now(),
                    'signal_id': f"BUY_{datetime.now().strftime('%H%M%S')}",
                    'close': close_1,
                    'open': open_1,
                    'previous_close': close_2,
                    'price_difference': price_diff_1_2,
                    'candle_color': 'green',
                    'reasons': [f"Close[1]>Close[2] AND Green: {close_1:.2f}>{close_2:.2f} AND {close_1:.2f}>{open_1:.2f}"],
                    'symbol': candlestick_data.get('symbol', 'XAUUSD.v')
                }
                
                self._record_signal(signal_data)
                return signal_data
            
            # ตรวจสอบเงื่อนไข SELL
            condition_close_lower = close_1 < close_2   # Close[1] < Close[2]
            condition_red_candle = close_1 < open_1     # Close[1] < Open[1] (แท่งแดง)
            
            print(f"SELL Conditions:")
            print(f"  Close[1] < Close[2]: {close_1:.2f} < {close_2:.2f} = {condition_close_lower}")
            print(f"  Close[1] < Open[1]: {close_1:.2f} < {open_1:.2f} = {condition_red_candle}")
            
            if condition_close_lower and condition_red_candle and abs(price_diff_1_2) >= min_price_diff:
                signal_strength = min(abs(price_diff_1_2) / 2.0, 1.0)
                
                print(f"✅ SELL SIGNAL: แท่งแดงปิดต่ำกว่าแท่งก่อน")
                
                signal_data = {
                    'action': 'SELL',
                    'strength': signal_strength,
                    'confidence': signal_strength,
                    'timestamp': datetime.now(),
                    'signal_id': f"SELL_{datetime.now().strftime('%H%M%S')}",
                    'close': close_1,
                    'open': open_1,
                    'previous_close': close_2,
                    'price_difference': price_diff_1_2,
                    'candle_color': 'red',
                    'reasons': [f"Close[1]<Close[2] AND Red: {close_1:.2f}<{close_2:.2f} AND {close_1:.2f}<{open_1:.2f}"],
                    'symbol': candlestick_data.get('symbol', 'XAUUSD.v')
                }
                
                self._record_signal(signal_data)
                return signal_data
            
            # ไม่ตรงเงื่อนไข
            print(f"⏳ WAIT: เงื่อนไขไม่ครบ")
            if not condition_close_higher and not condition_close_lower:
                reason = "Close เท่ากัน"
            elif condition_close_higher and not condition_green_candle:
                reason = "ปิดสูงกว่าแต่ไม่เป็นแท่งเขียว"
            elif condition_close_lower and not condition_red_candle:
                reason = "ปิดต่ำกว่าแต่ไม่เป็นแท่งแดง"
            else:
                reason = "ต่างกันน้อย"
                
            return self._create_wait_signal(reason)
            
        except Exception as e:
            print(f"Signal error: {e}")
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
    
