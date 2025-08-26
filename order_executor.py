"""
⚡ Pure Market Order Executor
order_executor.py

🚀 Features:
✅ Market Orders เท่านั้น (ไม่มี pending orders)
✅ Dynamic Lot Size Calculation  
✅ Immediate Execution
✅ Execution Tracking & Statistics
✅ Error Handling & Retry Logic
✅ Slippage Monitoring

🎯 รับ signals จาก SignalGenerator แล้วส่งออเดอร์ทันที
ไม่มี Grid concepts - เป็น Pure Candlestick execution
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
        📤 ส่ง Market Order ผ่าน MT5
        
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
                    print(f"   Volume: {lot_size} lots")
                    print(f"   Symbol: {self.symbol}")
                    
                    # ส่งออเดอร์ผ่าน MT5
                    result = mt5.order_send(order_request)
                    
                    if result is None:
                        last_error = "MT5 order_send returned None"
                        print(f"❌ Attempt {attempt + 1}: {last_error}")
                        time.sleep(self.retry_delay)
                        continue
                    
                    # ตรวจสอบผลลัพธ์
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
        📋 เตรียม Order Request สำหรับ MT5
        
        Args:
            order_type: 'BUY' หรือ 'SELL'
            lot_size: ขนาด lot
            signal_data: ข้อมูล signal
            
        Returns:
            Dict: Order request object สำหรับ mt5.order_send()
        """
        try:
            # ดึงราคาปัจจุบัน
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                print(f"❌ Cannot get tick for {self.symbol}")
                return None
            
            # กำหนดราคาและประเภทออเดอร์
            if order_type == 'BUY':
                action = mt5.TRADE_ACTION_DEAL
                order_type_mt5 = mt5.ORDER_TYPE_BUY
                price = tick.ask  # ซื้อที่ราคา ask
            elif order_type == 'SELL':
                action = mt5.TRADE_ACTION_DEAL  
                order_type_mt5 = mt5.ORDER_TYPE_SELL
                price = tick.bid  # ขายที่ราคา bid
            else:
                print(f"❌ Invalid order type: {order_type}")
                return None
            
            # สร้าง order request
            order_request = {
                'action': action,
                'symbol': self.symbol,
                'volume': lot_size,
                'type': order_type_mt5,
                'price': price,
                'deviation': self.max_slippage,  # slippage tolerance
                'magic': self._generate_magic_number(signal_data),
                'comment': self._generate_order_comment(signal_data),
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': mt5.ORDER_FILLING_IOC  # Immediate or Cancel
            }
            
            print(f"📋 Order request prepared:")
            print(f"   Action: {order_type}")
            print(f"   Price: ${price:.2f}")
            print(f"   Volume: {lot_size} lots")
            print(f"   Max slippage: {self.max_slippage} points")
            
            return order_request
            
        except Exception as e:
            print(f"❌ Order request preparation error: {e}")
            return None
    
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
            equity = account_info.get('equity', balance)
            free_margin = account_info.get('free_margin', equity * 0.8)
            
            # ขนาด lot ตาม signal strength
            signal_strength = signal_data.get('strength', 0.6)
            lot_multiplier = signal_data.get('recommended_lot_multiplier', 1.0)
            
            # คำนวณ lot ตาม risk percentage
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                print(f"⚠️ No symbol info - using base lot")
                return self.base_lot
            
            # คำนวณ lot ตามความเสี่ยง
            tick_value = symbol_info.trade_tick_value
            tick_size = symbol_info.trade_tick_size
            
            if tick_value > 0 and tick_size > 0:
                # คำนวณ risk amount
                risk_amount = balance * (self.risk_percentage / 100.0)
                
                # ประมาณ stop loss distance (ใช้ 50 pips เป็น default)
                estimated_sl_points = 50
                estimated_sl_value = (estimated_sl_points * tick_size) * (tick_value / tick_size)
                
                # คำนวณ lot size
                risk_based_lot = risk_amount / estimated_sl_value if estimated_sl_value > 0 else self.base_lot
                
                # ปรับตาม signal strength และ multiplier
                final_lot = risk_based_lot * signal_strength * lot_multiplier
                
            else:
                # Fallback calculation
                final_lot = self.base_lot * signal_strength * lot_multiplier
            
            # ปรับตาม balance brackets
            final_lot = self._apply_balance_scaling(final_lot, balance)
            
            # จำกัดภายในขอบเขตที่กำหนด
            final_lot = max(self.min_lot, min(self.max_lot, final_lot))
            
            # ปัดเศษตาม symbol lot step
            final_lot = self._round_lot_size(final_lot)
            
            print(f"📏 Lot calculation:")
            print(f"   Balance: ${balance:.2f}")
            print(f"   Risk: {self.risk_percentage}%")
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
            balance_config = self.lot_config.get("account_factor", {})
            
            if balance >= balance_config.get("balance_threshold_3", 10000):
                scale_factor = 3.0
            elif balance >= balance_config.get("balance_threshold_2", 5000):
                scale_factor = 2.0  
            elif balance >= balance_config.get("balance_threshold_1", 1000):
                scale_factor = 1.5
            else:
                scale_factor = 1.0
            
            return lot_size * scale_factor
            
        except Exception as e:
            print(f"❌ Balance scaling error: {e}")
            return lot_size
    
    def _round_lot_size(self, lot_size: float) -> float:
        """🎯 ปัดเศษ Lot Size ตาม Symbol Requirements"""
        try:
            # ดึงข้อมูล symbol เพื่อดู lot step
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info and hasattr(symbol_info, 'volume_step'):
                step = symbol_info.volume_step
                rounded_lot = round(lot_size / step) * step
                return max(self.min_lot, rounded_lot)
            
            # Default: ปัดเป็น 0.01
            return round(lot_size, 2)
            
        except Exception as e:
            print(f"❌ Lot rounding error: {e}")
            return round(lot_size, 2)
    
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
            
            # ตรวจสอบการเชื่อมต่อ MT5
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
            # ใช้ timestamp และ signal type
            timestamp = int(datetime.now().timestamp()) % 100000  # เอา 5 หลักท้าย
            signal_type = 1 if signal_data.get('action') == 'BUY' else 2
            
            # รวม: 12345X (X = signal type)
            magic = int(f"{timestamp}{signal_type}")
            
            return magic
            
        except Exception as e:
            print(f"❌ Magic number generation error: {e}")
            return 123456  # Default magic
    
    def _generate_order_comment(self, signal_data: Dict) -> str:
        """💬 สร้าง Comment สำหรับ Order"""
        try:
            action = signal_data.get('action', 'UNKNOWN')
            strength = signal_data.get('strength', 0)
            pattern = signal_data.get('pattern_name', '')
            
            comment = f"Pure_{action}_S{strength:.2f}"
            
            if pattern and pattern != 'standard':
                comment += f"_{pattern}"
            
            # จำกัดความยาว comment
            return comment[:31]  # MT5 limit
            
        except Exception as e:
            print(f"❌ Comment generation error: {e}")
            return "PureCandlestick"
    
    def _calculate_slippage(self, order_type: str, signal_data: Dict, result) -> float:
        """📊 คำนวณ Slippage"""
        try:
            expected_price = signal_data.get('close', 0)  # ราคาที่คาดหวัง
            executed_price = float(result.price)
            
            if expected_price <= 0:
                return 0.0
            
            # คำนวณ slippage เป็น points
            if order_type == 'BUY':
                slippage = (executed_price - expected_price) * 10000  # แปลงเป็น points
            else:  # SELL
                slippage = (expected_price - executed_price) * 10000
            
            return round(slippage, 1)
            
        except Exception as e:
            print(f"❌ Slippage calculation error: {e}")
            return 0.0
    
    # ==========================================
    # 📊 STATISTICS & TRACKING
    # ==========================================
    
    def _record_execution_stats(self, execution_result: Dict, signal_data: Dict):
        """📝 บันทึกสถิติการส่งออเดอร์"""
        try:
            self.execution_stats['total_orders'] += 1
            self.execution_stats['last_order_time'] = datetime.now()
            
            if execution_result and execution_result.get('success'):
                self.execution_stats['successful_orders'] += 1
                
                # บันทึกตาม order type
                action = signal_data.get('action')
                if action == 'BUY':
                    self.execution_stats['buy_orders'] += 1
                elif action == 'SELL':
                    self.execution_stats['sell_orders'] += 1
                
                # บันทึก volume และ execution time
                volume = execution_result.get('volume', 0)
                exec_time = execution_result.get('execution_time_ms', 0)
                slippage = execution_result.get('slippage_points', 0)
                
                self.execution_stats['total_volume'] += volume
                self.execution_stats['execution_times'].append(exec_time)
                self.execution_stats['total_slippage'] += abs(slippage)
                
                # เก็บแค่ 100 execution times ล่าสุด
                if len(self.execution_stats['execution_times']) > 100:
                    self.execution_stats['execution_times'] = self.execution_stats['execution_times'][-100:]
                    
            else:
                self.execution_stats['failed_orders'] += 1
                print(f"📊 Failed order recorded")
            
        except Exception as e:
            print(f"❌ Stats recording error: {e}")
    
    def _record_failed_execution(self, signal_data: Dict, error_msg: str):
        """❌ บันทึกการส่งออเดอร์ที่ไม่สำเร็จ"""
        try:
            self.execution_stats['total_orders'] += 1
            self.execution_stats['failed_orders'] += 1
            self.execution_stats['last_order_time'] = datetime.now()
            
            print(f"📊 Failed execution recorded: {error_msg}")
            
        except Exception as e:
            print(f"❌ Failed execution recording error: {e}")
    
    def get_execution_statistics(self) -> Dict:
        """📊 ดึงสถิติการส่งออเดอร์"""
        try:
            stats = self.execution_stats.copy()
            
            # คำนวณเพิ่มเติม
            total_orders = stats['total_orders']
            successful_orders = stats['successful_orders']
            
            stats['success_rate'] = (successful_orders / total_orders) if total_orders > 0 else 0
            stats['failure_rate'] = (stats['failed_orders'] / total_orders) if total_orders > 0 else 0
            
            # คำนวณ average execution time
            exec_times = stats['execution_times']
            stats['avg_execution_time_ms'] = (
                sum(exec_times) / len(exec_times) if exec_times else 0
            )
            
            # คำนวณ average slippage per order
            stats['avg_slippage_points'] = (
                stats['total_slippage'] / successful_orders if successful_orders > 0 else 0
            )
            
            # เพิ่มข้อมูล configuration
            stats['base_lot'] = self.base_lot
            stats['risk_percentage'] = self.risk_percentage
            stats['symbol'] = self.symbol
            
            return stats
            
        except Exception as e:
            print(f"❌ Statistics calculation error: {e}")
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