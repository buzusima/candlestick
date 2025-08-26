"""
⚡ Pure Market Order Executor (COMPLETE FIXED)
order_executor.py

🔧 ALL ISSUES FIXED:
✅ Indentation errors
✅ Method signatures
✅ OHLC data handling
✅ Symbol detection
✅ Order execution logic

🚀 Features:
✅ Market Orders เท่านั้น (ไม่มี pending orders)
✅ Dynamic Lot Size Calculation  
✅ Immediate Execution
✅ Execution Tracking & Statistics
✅ Error Handling & Retry Logic
✅ Slippage Monitoring
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

class OrderExecutor:
    """
    ⚡ Pure Market Order Executor
    
    รับ signals แล้วส่ง Market Orders ผ่าน MT5
    เน้นความเร็วและความถูกต้อง
    """
    
    def __init__(self, mt5_connector, config: Dict):
        """
        🔧 เริ่มต้น Order Executor
        
        Args:
            mt5_connector: MT5 connection object
            config: การตั้งค่าระบบ
        """
        self.mt5_connector = mt5_connector
        self.config = config
        
        # การตั้งค่าการเทรด
        self.trading_config = config.get("trading", {})
        self.symbol = self.trading_config.get("symbol", "XAUUSD.v")
        
        # Lot sizing configuration
        self.lot_config = config.get("lot_sizing", {})
        self.base_lot = self.lot_config.get("base_lot", 0.01)
        self.min_lot = self.lot_config.get("min_lot", 0.01)
        self.max_lot = self.lot_config.get("max_lot", 1.0)
        self.risk_percentage = self.lot_config.get("risk_percentage", 2.0)
        
        # Execution settings
        self.retry_attempts = 3
        self.retry_delay = 0.5  # วินาที
        self.max_slippage = 10  # points
        
        # Statistics tracking
        self.execution_stats = {
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'buy_orders': 0,
            'sell_orders': 0,
            'total_volume': 0.0,
            'total_slippage': 0.0,
            'execution_times': [],
            'last_order_time': datetime.min
        }
        
        print(f"⚡ Order Executor initialized for {self.symbol}")
        print(f"   Base lot: {self.base_lot}")
        print(f"   Risk: {self.risk_percentage}% per trade")
        print(f"   Max retries: {self.retry_attempts}")
    
    # ==========================================
    # ⚡ MAIN EXECUTION METHODS
    # ==========================================
    
    def execute_signal(self, signal_data: Dict) -> Optional[Dict]:
        """
        ⚡ ส่งออเดอร์ตาม Signal ที่ได้รับ
        
        Args:
            signal_data: ข้อมูล signal จาก SignalGenerator
            
        Returns:
            Dict: ผลการส่งออเดอร์ หรือ None ถ้าไม่ส่ง
        """
        try:
            # ตรวจสอบ signal
            if not self._validate_signal(signal_data):
                return None
            
            action = signal_data.get('action')
            
            if action not in ['BUY', 'SELL']:
                print(f"ℹ️ No execution needed for action: {action}")
                return None
            
            print(f"⚡ Executing {action} signal...")
            print(f"   Signal strength: {signal_data.get('strength', 0):.2f}")
            print(f"   Signal ID: {signal_data.get('signal_id', 'unknown')}")
            
            # คำนวณ lot size
            lot_size = self._calculate_lot_size(signal_data)
            if lot_size <= 0:
                print(f"❌ Invalid lot size calculated: {lot_size}")
                return None
            
            # ส่งออเดอร์ Market
            execution_result = self._send_market_order(action, lot_size, signal_data)
            
            # บันทึกสถิติ
            self._record_execution_stats(execution_result, signal_data)
            
            return execution_result
            
        except Exception as e:
            print(f"❌ Signal execution error: {e}")
            self._record_failed_execution(signal_data, str(e))
            return None
    
    def _send_market_order(self, order_type: str, lot_size: float, signal_data: Dict) -> Optional[Dict]:
        """
        📤 ส่ง Market Order ผ่าน MT5 (COMPLETE FIXED)
        
        Args:
            order_type: 'BUY' หรือ 'SELL'
            lot_size: ขนาด lot
            signal_data: ข้อมูล signal
            
        Returns:
            Dict: ผลการส่งออเดอร์
        """
        try:
            if not self.mt5_connector.is_connected:
                print(f"❌ MT5 not connected - cannot send order")
                return None
            
            # ตรวจสอบ account permissions
            account_info = mt5.account_info()
            if account_info is None:
                print(f"❌ Cannot get account info")
                return None
            
            if not account_info.trade_allowed:
                print(f"❌ Trading not allowed on this account")
                return None
            
            print(f"✅ Account trading permissions OK")
            
            # เตรียม order request
            order_request = self._prepare_order_request(order_type, lot_size, signal_data)
            
            if not order_request:
                print(f"❌ Failed to prepare order request")
                return None
            
            execution_start = time.time()
            
            # ส่งออเดอร์พร้อม retry logic
            order_result = None
            last_error = ""
            
            for attempt in range(self.retry_attempts):
                try:
                    print(f"📤 Sending {order_type} order (Attempt {attempt + 1}/{self.retry_attempts})...")
                    
                    # ส่งออเดอร์ผ่าน MT5
                    result = mt5.order_send(order_request)
                    
                    print(f"🔍 MT5 order_send result type: {type(result)}")
                    print(f"🔍 MT5 order_send result: {result}")
                    
                    if result is None:
                        last_error = "MT5 order_send returned None"
                        print(f"❌ Attempt {attempt + 1}: {last_error}")
                        
                        # Debug: เช็ค MT5 terminal status
                        terminal_info = mt5.terminal_info()
                        if terminal_info:
                            print(f"🔍 Terminal connected: {terminal_info.connected}")
                            print(f"🔍 Terminal trade allowed: {terminal_info.trade_allowed}")
                        
                        time.sleep(self.retry_delay)
                        continue
                    
                    # ตรวจสอบผลลัพธ์
                    print(f"🔍 Result retcode: {result.retcode}")
                    
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        execution_time = time.time() - execution_start
                        
                        order_result = {
                            'success': True,
                            'order_id': result.order,
                            'deal_id': result.deal,
                            'volume': result.volume,
                            'price': result.price,
                            'bid': result.bid,
                            'ask': result.ask,
                            'execution_time_ms': round(execution_time * 1000, 2),
                            'retcode': result.retcode,
                            'comment': result.comment
                        }
                        
                        # คำนวณ slippage
                        slippage = self._calculate_slippage(order_type, signal_data, result)
                        order_result['slippage_points'] = slippage
                        
                        print(f"✅ Order executed successfully!")
                        print(f"   Order ID: {result.order}")
                        print(f"   Deal ID: {result.deal}")
                        print(f"   Price: ${result.price:.2f}")
                        print(f"   Volume: {result.volume} lots")
                        print(f"   Execution: {execution_time*1000:.1f}ms")
                        print(f"   Slippage: {slippage:.1f} points")
                        
                        break
                        
                    else:
                        last_error = f"Order failed: {result.retcode} - {result.comment}"
                        print(f"❌ Attempt {attempt + 1}: {last_error}")
                        
                        # อธิบาย error code
                        self._explain_error_code(result.retcode)
                        
                        if attempt < self.retry_attempts - 1:
                            time.sleep(self.retry_delay)
                        
                except Exception as e:
                    last_error = f"Exception: {str(e)}"
                    print(f"❌ Attempt {attempt + 1}: {last_error}")
                    
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
            
            # ถ้าส่งไม่สำเร็จทุก attempts
            if not order_result:
                execution_time = time.time() - execution_start
                order_result = {
                    'success': False,
                    'error': last_error,
                    'execution_time_ms': round(execution_time * 1000, 2),
                    'attempts': self.retry_attempts
                }
                print(f"❌ Order execution failed after {self.retry_attempts} attempts")
                print(f"   Final error: {last_error}")
            
            return order_result
            
        except Exception as e:
            print(f"❌ Send market order error: {e}")
            return {
                'success': False,
                'error': f"Execution error: {str(e)}",
                'execution_time_ms': 0,
                'attempts': 0
            }
    
    def _prepare_order_request(self, order_type: str, lot_size: float, signal_data: Dict) -> Optional[Dict]:
        """
        📋 เตรียม Order Request สำหรับ MT5 (COMPLETE FIXED)
        
        Args:
            order_type: 'BUY' หรือ 'SELL'
            lot_size: ขนาด lot
            signal_data: ข้อมูล signal
            
        Returns:
            Dict: Order request object สำหรับ mt5.order_send()
        """
        try:
            print(f"🔧 Preparing {order_type} order request...")
            
            # ตรวจสอบ symbol
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                print(f"❌ Symbol {self.symbol} not found, trying alternatives...")
                
                # ลองหา alternative symbols
                alternative_symbols = ["XAUUSD", "GOLD", "#GOLD", "XAUUSD.", "XAU/USD"]
                for alt_symbol in alternative_symbols:
                    alt_info = mt5.symbol_info(alt_symbol)
                    if alt_info is not None:
                        print(f"💡 Found alternative symbol: {alt_symbol}")
                        self.symbol = alt_symbol
                        symbol_info = alt_info
                        break
                
                if symbol_info is None:
                    print(f"❌ No valid gold symbol found")
                    return None
            
            # ทำให้ symbol visible
            if not symbol_info.visible:
                print(f"🔧 Making symbol {self.symbol} visible...")
                if not mt5.symbol_select(self.symbol, True):
                    print(f"❌ Cannot make symbol visible")
                    return None
                time.sleep(0.2)
            
            # ตรวจสอบ trade permissions
            if hasattr(symbol_info, 'trade_mode') and symbol_info.trade_mode == 0:
                print(f"❌ Trading disabled for symbol {self.symbol}")
                return None
            
            # ดึงราคาปัจจุบัน
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                print(f"❌ Cannot get tick for {self.symbol}")
                return None
            
            if tick.bid <= 0 or tick.ask <= 0:
                print(f"❌ Invalid prices: Bid {tick.bid}, Ask {tick.ask}")
                return None
            
            print(f"💰 Current prices: Bid ${tick.bid:.2f}, Ask ${tick.ask:.2f}")
            
            # ปรับ lot size ตาม symbol requirements
            min_volume = symbol_info.volume_min
            max_volume = symbol_info.volume_max  
            volume_step = symbol_info.volume_step
            
            print(f"📏 Volume limits: Min {min_volume}, Max {max_volume}, Step {volume_step}")
            
            # ปรับ lot size
            if lot_size < min_volume:
                lot_size = min_volume
                print(f"🔧 Lot adjusted to minimum: {lot_size}")
            elif lot_size > max_volume:
                lot_size = max_volume
                print(f"🔧 Lot adjusted to maximum: {lot_size}")
            
            # ปัดตาม step
            if volume_step > 0:
                steps = round(lot_size / volume_step)
                lot_size = steps * volume_step
                lot_size = max(min_volume, lot_size)
                print(f"🔧 Lot rounded to step: {lot_size}")
            
            # กำหนดราคาและประเภทออเดอร์
            if order_type == 'BUY':
                action = mt5.TRADE_ACTION_DEAL
                order_type_mt5 = mt5.ORDER_TYPE_BUY
                price = tick.ask
            elif order_type == 'SELL':
                action = mt5.TRADE_ACTION_DEAL  
                order_type_mt5 = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                print(f"❌ Invalid order type: {order_type}")
                return None
            
            # สร้าง order request (แบบง่ายที่สุด)
            order_request = {
                'action': action,
                'symbol': self.symbol,
                'volume': lot_size,
                'type': order_type_mt5,
                'price': price,
                'deviation': self.max_slippage,
                'magic': self._generate_magic_number(signal_data),
                'comment': self._generate_order_comment(signal_data)
            }
            
            print(f"📋 Order request prepared:")
            print(f"   Symbol: {self.symbol}")
            print(f"   Action: {order_type}")
            print(f"   Price: ${price:.2f}")
            print(f"   Volume: {lot_size} lots")
            print(f"   Magic: {order_request['magic']}")
            
            return order_request
            
        except Exception as e:
            print(f"❌ Order request preparation error: {e}")
            return None
    
    def _explain_error_code(self, retcode: int):
        """🔍 อธิบาย MT5 Error Codes"""
        error_codes = {
            10004: "REQUOTE - Price changed",
            10006: "REJECT - Request rejected", 
            10009: "DONE - Request completed",
            10013: "INVALID - Invalid request",
            10014: "INVALID_VOLUME - Invalid volume",
            10015: "INVALID_PRICE - Invalid price", 
            10017: "TRADE_DISABLED - Trading disabled",
            10018: "MARKET_CLOSED - Market closed",
            10019: "NO_MONEY - Not enough money",
            10030: "INVALID_FILL - Invalid filling type",
            10031: "CONNECTION - No connection"
        }
        
        explanation = error_codes.get(retcode, f"Unknown error code: {retcode}")
        print(f"🔍 Error {retcode}: {explanation}")
    
    # ==========================================
    # 📏 LOT SIZE CALCULATION
    # ==========================================
    
    def _calculate_lot_size(self, signal_data: Dict) -> float:
        """
        📏 คำนวณ Lot Size แบบ Dynamic
        
        Args:
            signal_data: ข้อมูล signal
            
        Returns:
            float: ขนาด lot ที่เหมาะสม
        """
        try:
            # ดึงข้อมูลบัญชี
            if not self.mt5_connector.is_connected:
                print(f"❌ MT5 not connected - using base lot")
                return self.base_lot
            
            account_info = self.mt5_connector.get_account_info()
            if not account_info:
                print(f"⚠️ No account info - using base lot")
                return self.base_lot
            
            balance = account_info.get('balance', 10000)
            signal_strength = signal_data.get('strength', 0.6)
            lot_multiplier = signal_data.get('recommended_lot_multiplier', 1.0)
            
            # คำนวณ lot แบบง่าย
            final_lot = self.base_lot * signal_strength * lot_multiplier
            
            # ปรับตาม balance
            final_lot = self._apply_balance_scaling(final_lot, balance)
            
            # จำกัดขอบเขต
            final_lot = max(self.min_lot, min(self.max_lot, final_lot))
            final_lot = round(final_lot, 2)
            
            print(f"📏 Lot calculation:")
            print(f"   Balance: ${balance:.2f}")
            print(f"   Signal strength: {signal_strength:.2f}")
            print(f"   Multiplier: {lot_multiplier:.2f}")
            print(f"   Final lot: {final_lot:.2f}")
            
            return final_lot
            
        except Exception as e:
            print(f"❌ Lot calculation error: {e}")
            return self.base_lot
    
    def _apply_balance_scaling(self, lot_size: float, balance: float) -> float:
        """📊 ปรับ Lot Size ตาม Balance"""
        try:
            if balance >= 10000:
                scale_factor = 2.0
            elif balance >= 5000:
                scale_factor = 1.5
            elif balance >= 1000:
                scale_factor = 1.0
            else:
                scale_factor = 0.5
            
            return lot_size * scale_factor
            
        except Exception as e:
            return lot_size
    
    # ==========================================
    # 🔧 HELPER METHODS
    # ==========================================
    
    def _validate_signal(self, signal_data: Dict) -> bool:
        """✅ ตรวจสอบความถูกต้องของ Signal"""
        try:
            if not signal_data:
                print(f"❌ Empty signal data")
                return False
            
            action = signal_data.get('action')
            if action not in ['BUY', 'SELL', 'WAIT']:
                print(f"❌ Invalid signal action: {action}")
                return False
            
            if action in ['BUY', 'SELL']:
                strength = signal_data.get('strength', 0)
                if strength <= 0:
                    print(f"❌ Invalid signal strength: {strength}")
                    return False
            
            if not self.mt5_connector.is_connected:
                print(f"❌ MT5 not connected")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Signal validation error: {e}")
            return False
    
    def _generate_magic_number(self, signal_data: Dict) -> int:
        """🎲 สร้าง Magic Number สำหรับ Order"""
        try:
            timestamp = int(datetime.now().timestamp()) % 100000
            signal_type = 1 if signal_data.get('action') == 'BUY' else 2
            magic = int(f"{timestamp}{signal_type}")
            return magic
        except Exception as e:
            return 123456
    
    def _generate_order_comment(self, signal_data: Dict) -> str:
        """💬 สร้าง Comment สำหรับ Order"""
        try:
            action = signal_data.get('action', 'UNKNOWN')
            strength = signal_data.get('strength', 0)
            comment = f"Pure_{action}_S{strength:.2f}"
            return comment[:31]
        except Exception as e:
            return "PureCandlestick"
    
    def _calculate_slippage(self, order_type: str, signal_data: Dict, result) -> float:
        """📊 คำนวณ Slippage"""
        try:
            expected_price = signal_data.get('close', 0)
            executed_price = float(result.price)
            
            if expected_price <= 0:
                return 0.0
            
            if order_type == 'BUY':
                slippage = (executed_price - expected_price) * 10000
            else:
                slippage = (expected_price - executed_price) * 10000
            
            return round(slippage, 1)
            
        except Exception as e:
            return 0.0
    
    # ==========================================
    # 📊 STATISTICS METHODS
    # ==========================================
    
    def _record_execution_stats(self, execution_result: Dict, signal_data: Dict):
        """📝 บันทึกสถิติการส่งออเดอร์"""
        try:
            self.execution_stats['total_orders'] += 1
            self.execution_stats['last_order_time'] = datetime.now()
            
            if execution_result and execution_result.get('success'):
                self.execution_stats['successful_orders'] += 1
                
                action = signal_data.get('action')
                if action == 'BUY':
                    self.execution_stats['buy_orders'] += 1
                elif action == 'SELL':
                    self.execution_stats['sell_orders'] += 1
                
                volume = execution_result.get('volume', 0)
                exec_time = execution_result.get('execution_time_ms', 0)
                slippage = execution_result.get('slippage_points', 0)
                
                self.execution_stats['total_volume'] += volume
                self.execution_stats['execution_times'].append(exec_time)
                self.execution_stats['total_slippage'] += abs(slippage)
                
                if len(self.execution_stats['execution_times']) > 100:
                    self.execution_stats['execution_times'] = self.execution_stats['execution_times'][-100:]
                    
            else:
                self.execution_stats['failed_orders'] += 1
            
        except Exception as e:
            print(f"❌ Stats recording error: {e}")
    
    def _record_failed_execution(self, signal_data: Dict, error_msg: str):
        """❌ บันทึกการส่งออเดอร์ที่ไม่สำเร็จ"""
        try:
            self.execution_stats['total_orders'] += 1
            self.execution_stats['failed_orders'] += 1
            self.execution_stats['last_order_time'] = datetime.now()
        except Exception as e:
            print(f"❌ Failed execution recording error: {e}")
    
    def get_execution_statistics(self) -> Dict:
        """📊 ดึงสถิติการส่งออเดอร์"""
        try:
            stats = self.execution_stats.copy()
            
            total_orders = stats['total_orders']
            successful_orders = stats['successful_orders']
            
            stats['success_rate'] = (successful_orders / total_orders) if total_orders > 0 else 0
            stats['failure_rate'] = (stats['failed_orders'] / total_orders) if total_orders > 0 else 0
            
            exec_times = stats['execution_times']
            stats['avg_execution_time_ms'] = sum(exec_times) / len(exec_times) if exec_times else 0
            stats['avg_slippage_points'] = stats['total_slippage'] / successful_orders if successful_orders > 0 else 0
            
            stats['base_lot'] = self.base_lot
            stats['risk_percentage'] = self.risk_percentage
            stats['symbol'] = self.symbol
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
    
    def is_ready(self) -> bool:
        """✅ ตรวจสอบความพร้อม"""
        return (
            self.mt5_connector is not None and
            self.mt5_connector.is_connected and
            self.symbol is not None
        )
    
    def get_executor_info(self) -> Dict:
        """ℹ️ ข้อมูล Order Executor"""
        return {
            'name': 'Pure Market Order Executor',
            'version': '1.0.0',
            'symbol': self.symbol,
            'order_types': ['Market BUY', 'Market SELL'],
            'base_lot': self.base_lot,
            'min_lot': self.min_lot,
            'max_lot': self.max_lot,
            'risk_percentage': self.risk_percentage,
            'retry_attempts': self.retry_attempts,
            'max_slippage': self.max_slippage
        }