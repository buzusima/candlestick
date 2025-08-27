"""
🔍 Test Rates Debug - ทดสอบดึงข้อมูล rates[0][1][2] ทั้งหมด
test_rates_debug.py

🎯 วัตถุประสงค์:
✅ ดูข้อมูล rates[0], rates[1], rates[2] ทั้งหมด
✅ เปรียบเทียบกับกราฟที่เห็น
✅ เช็คว่า Low[1] ถูกต้องหรือไม่
✅ หาสาเหตุที่ข้อมูลไม่ตรงกราฟ
"""

import MetaTrader5 as mt5
from datetime import datetime
import sys
import os

class RatesDebugger:
    """🔍 ตัวทดสอบดึงข้อมูล rates จาก MT5"""
    
    def __init__(self):
        self.symbol = "XAUUSD.v"  # ปรับตาม symbol ที่ใช้
        self.timeframe = mt5.TIMEFRAME_M5
        
    def connect_mt5(self) -> bool:
        """เชื่อมต่อ MT5"""
        try:
            print("🔗 กำลังเชื่อมต่อ MT5...")
            
            if not mt5.initialize():
                print("❌ ไม่สามารถเชื่อมต่อ MT5 ได้")
                return False
            
            account_info = mt5.account_info()
            if account_info is None:
                print("❌ ไม่มีข้อมูล account")
                return False
            
            print(f"✅ เชื่อมต่อ MT5 สำเร็จ")
            print(f"   Account: {account_info.login}")
            print(f"   Company: {account_info.company}")
            print(f"   Balance: ${account_info.balance:,.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ เชื่อมต่อ MT5 ผิดพลาด: {e}")
            return False
    
    def debug_all_rates(self):
        """🔍 ดีบักข้อมูล rates ทั้งหมด"""
        try:
            print(f"\n=== 🔍 DEBUG ALL RATES FOR {self.symbol} ===")
            print("=" * 60)
            
            # ดึงข้อมูล rates
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 5)
            
            if rates is None:
                print(f"❌ ไม่สามารถดึง rates สำหรับ {self.symbol}")
                print("💡 ลองเช็ค:")
                print("   - Symbol ถูกต้องไหม?")
                print("   - MT5 เปิดกราฟ symbol นี้ไหม?")
                return
            
            print(f"✅ ได้ข้อมูล {len(rates)} แท่งจาก MT5")
            print()
            
            # แสดงข้อมูลแต่ละแท่ง
            for i, rate in enumerate(rates):
                timestamp = int(rate['time'])
                candle_time = datetime.fromtimestamp(timestamp)
                
                # แปลงข้อมูล OHLC
                open_price = float(rate['open'])
                high_price = float(rate['high'])
                low_price = float(rate['low'])
                close_price = float(rate['close'])
                volume = int(rate['tick_volume']) if 'tick_volume' in rate.dtype.names else 0
                
                # กำหนดสีแท่ง
                if close_price > open_price:
                    color = "🟢 GREEN (Bull)"
                elif close_price < open_price:
                    color = "🔴 RED (Bear)"
                else:
                    color = "⚪ DOJI"
                
                # คำนวณข้อมูลเพิ่มเติม
                body_size = abs(close_price - open_price)
                candle_range = high_price - low_price
                body_ratio = body_size / candle_range if candle_range > 0 else 0
                
                upper_wick = high_price - max(open_price, close_price)
                lower_wick = min(open_price, close_price) - low_price
                
                print(f"📊 RATES[{i}] - {candle_time.strftime('%H:%M:%S')} {color}")
                print(f"   📍 Time: {candle_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   💰 OHLC: O:{open_price:.4f} H:{high_price:.4f} L:{low_price:.4f} C:{close_price:.4f}")
                print(f"   📊 Body: {body_size:.4f} ({body_ratio:.2%}) | Range: {candle_range:.4f}")
                print(f"   🕯️ Wicks: Upper:{upper_wick:.4f} Lower:{lower_wick:.4f}")
                print(f"   📈 Volume: {volume:,}")
                print()
            
            print("=" * 60)
            
            # เปรียบเทียบตามเงื่อนไขใหม่
            print(f"🎯 CONDITION ANALYSIS:")
            
            if len(rates) >= 2:
                close_0 = float(rates[0]['close'])
                high_1 = float(rates[1]['high'])
                low_1 = float(rates[1]['low'])
                
                print(f"   Close[0]: {close_0:.4f} (แท่งปัจจุบัน)")
                print(f"   High[1]:  {high_1:.4f} (จุดสูงสุดแท่งที่ปิดล่าสุด)")
                print(f"   Low[1]:   {low_1:.4f} (จุดต่ำสุดแท่งที่ปิดล่าสุด)")
                print()
                
                # เช็คเงื่อนไข
                if close_0 > high_1:
                    breakout = close_0 - high_1
                    print(f"🟢 BUY CONDITION MET!")
                    print(f"   Close[0] {close_0:.4f} > High[1] {high_1:.4f}")
                    print(f"   Breakout: +{breakout:.4f}")
                    
                elif close_0 < low_1:
                    breakdown = low_1 - close_0
                    print(f"🔴 SELL CONDITION MET!")
                    print(f"   Close[0] {close_0:.4f} < Low[1] {low_1:.4f}")
                    print(f"   Breakdown: -{breakdown:.4f}")
                    
                else:
                    print(f"⏳ NO SIGNAL - ราคาอยู่ในช่วง:")
                    print(f"   Low[1] {low_1:.4f} <= Close[0] {close_0:.4f} <= High[1] {high_1:.4f}")
                    margin_to_high = high_1 - close_0
                    margin_to_low = close_0 - low_1
                    print(f"   ห่างจาก High[1]: {margin_to_high:.4f}")
                    print(f"   ห่างจาก Low[1]: {margin_to_low:.4f}")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Debug rates error: {e}")
            import traceback
            traceback.print_exc()
    
    def compare_with_current_price(self):
        """🔍 เปรียบเทียบกับราคาปัจจุบัน"""
        try:
            print(f"\n=== 🔍 CURRENT PRICE COMPARISON ===")
            
            # ดึงราคาปัจจุบัน
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                print(f"❌ ไม่สามารถดึงราคาปัจจุบันสำหรับ {self.symbol}")
                return
            
            print(f"💰 ราคาปัจจุบัน (Tick):")
            print(f"   Bid: {tick.bid:.4f}")
            print(f"   Ask: {tick.ask:.4f}")
            print(f"   Time: {datetime.fromtimestamp(tick.time).strftime('%H:%M:%S')}")
            
            # เปรียบเทียบกับ rates[0]
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 1)
            if rates is not None and len(rates) > 0:
                rate_close = float(rates[0]['close'])
                print(f"   Rate[0] Close: {rate_close:.4f}")
                print(f"   ต่างจาก Bid: {abs(tick.bid - rate_close):.4f}")
                print(f"   ต่างจาก Ask: {abs(tick.ask - rate_close):.4f}")
            
        except Exception as e:
            print(f"❌ Current price comparison error: {e}")
    
    def test_symbol_info(self):
        """🔍 ทดสอบข้อมูล Symbol"""
        try:
            print(f"\n=== 🔍 SYMBOL INFO TEST ===")
            
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                print(f"❌ Symbol {self.symbol} ไม่พบ")
                
                # ลองหา symbol ที่คล้าย
                print("🔍 หา symbols ที่มี 'XAU' หรือ 'GOLD':")
                all_symbols = mt5.symbols_get()
                if all_symbols:
                    gold_symbols = [s.name for s in all_symbols if 'XAU' in s.name or 'GOLD' in s.name]
                    for sym in gold_symbols[:10]:  # แสดง 10 ตัวแรก
                        print(f"   - {sym}")
                return
            
            print(f"✅ Symbol {self.symbol} พบ:")
            print(f"   Name: {symbol_info.name}")
            print(f"   Visible: {symbol_info.visible}")
            print(f"   Digits: {symbol_info.digits}")
            print(f"   Point: {symbol_info.point}")
            print(f"   Min volume: {symbol_info.volume_min}")
            print(f"   Max volume: {symbol_info.volume_max}")
            
            if not symbol_info.visible:
                print("⚠️ Symbol ไม่ visible - ลอง select...")
                if mt5.symbol_select(self.symbol, True):
                    print("✅ Symbol selected successfully")
                else:
                    print("❌ ไม่สามารถ select symbol ได้")
            
        except Exception as e:
            print(f"❌ Symbol info test error: {e}")
    
    def disconnect_mt5(self):
        """ตัดการเชื่อมต่อ MT5"""
        try:
            mt5.shutdown()
            print("✅ ตัดการเชื่อมต่อ MT5 แล้ว")
        except:
            pass

def main():
    """🚀 เริ่มการทดสอบ"""
    
    print("🔍 RATES DATA DEBUGGER")
    print("=" * 60)
    print(f"⏰ เวลาทดสอบ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    debugger = RatesDebugger()
    
    # เชื่อมต่อ MT5
    if not debugger.connect_mt5():
        print("❌ ไม่สามารถเชื่อมต่อ MT5 ได้")
        return
    
    try:
        # ทดสอบข้อมูล symbol
        debugger.test_symbol_info()
        
        # ดีบัก rates data
        debugger.debug_all_rates()
        
        # เปรียบเทียบกับราคาปัจจุบัน
        debugger.compare_with_current_price()
        
        print("\n✅ การทดสอบเสร็จสิ้น")
        
    except KeyboardInterrupt:
        print("\n🛑 หยุดการทดสอบโดยผู้ใช้")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        debugger.disconnect_mt5()

if __name__ == "__main__":
    main()