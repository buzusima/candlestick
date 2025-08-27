"""
💰 Smart Position Monitor & Manager
position_monitor.py

🚀 Features:
✅ Real-time Position Monitoring
✅ Smart Recovery (หา profitable positions ชดเชย losing positions)
✅ Portfolio Balance Management
✅ Intelligent Close Combinations (ไม่ใช่ 1:1)
✅ Emergency Close Protocols
✅ Position Age & P&L Tracking

🎯 วิเคราะห์ positions และหาโอกาสปิดออเดอร์ที่เหมาะสม
เพื่อ optimize portfolio และลดความเสี่ยง
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import statistics
import time

class PositionMonitor:
    """
    💰 Smart Position Monitor & Manager
    
    ติดตามออเดอร์และหาโอกาสปิดออเดอร์อัจฉริยะ
    เน้น portfolio optimization และ risk management
    """
    
    def __init__(self, mt5_connector, config: Dict):
        """
        🔧 เริ่มต้น Position Monitor
        
        Args:
            mt5_connector: MT5 connection object
            config: การตั้งค่าระบบ
        """
        self.mt5_connector = mt5_connector
        self.config = config
        
        # การตั้งค่า position management
        self.position_config = config.get("position_management", {})
        self.symbol = config.get("trading", {}).get("symbol", "XAUUSD.v")
        
        # Smart close settings
        self.max_losing_age_hours = self.position_config.get("max_losing_age_hours", 24)
        self.min_profit_to_close = self.position_config.get("min_profit_to_close", 5.0)
        self.portfolio_balance_threshold = self.position_config.get("portfolio_balance_threshold", 0.7)
        
        # Emergency settings
        self.max_total_loss = self.position_config.get("max_total_loss", -500.0)
        self.max_single_loss = self.position_config.get("max_single_loss", -100.0)
        self.margin_level_warning = self.position_config.get("margin_level_warning", 200.0)
        
        # Tracking
        self.position_cache = {}
        self.last_update_time = datetime.min
        self.cache_duration_seconds = 5
        
        # Statistics
        self.close_stats = {
            'smart_closes': 0,
            'emergency_closes': 0,
            'profit_closes': 0,
            'recovery_closes': 0,
            'total_closed_profit': 0.0
        }
        
        print(f"💰 Position Monitor initialized for {self.symbol}")
        print(f"   Max losing age: {self.max_losing_age_hours}h")
        print(f"   Min profit to close: ${self.min_profit_to_close}")
        print(f"   Max total loss: ${self.max_total_loss}")
    
    # ==========================================
    # 📊 POSITION RETRIEVAL & MONITORING
    # ==========================================
    
    def get_all_positions(self) -> List[Dict]:
        """
        📊 ดึงออเดอร์ทั้งหมดที่เปิดอยู่ - FIXED Commission Error
        
        Returns:
            List[Dict]: รายการ positions พร้อมข้อมูลเพิ่มเติม
        """
        try:
            if not self.mt5_connector.is_connected:
                print(f"❌ MT5 not connected - cannot get positions")
                return []
            
            # ตรวจสอบ cache
            if self._is_cache_valid():
                return list(self.position_cache.values())
            
            # ดึงข้อมูล positions จาก MT5
            raw_positions = mt5.positions_get(symbol=self.symbol)
            
            if raw_positions is None:
                print(f"ℹ️ No positions found for {self.symbol}")
                self.position_cache = {}
                return []
            
            # แปลงและเพิ่มข้อมูล
            processed_positions = []
            current_time = datetime.now()
            
            for pos in raw_positions:
                try:
                    # 🔧 FIXED: ใช้ getattr เพื่อป้องกัน AttributeError
                    commission = getattr(pos, 'commission', 0.0)  # ป้องกัน commission ไม่มี
                    swap = getattr(pos, 'swap', 0.0)              # ป้องกัน swap ไม่มี
                    comment = getattr(pos, 'comment', '')         # ป้องกัน comment ไม่มี
                    magic = getattr(pos, 'magic', 0)              # ป้องกัน magic ไม่มี
                    
                    # แปลงข้อมูลพื้นฐาน
                    position_data = {
                        'id': pos.ticket,
                        'symbol': pos.symbol,
                        'type': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                        'volume': float(pos.volume),
                        'price_open': float(pos.price_open),
                        'price_current': float(pos.price_current),
                        'profit': float(pos.profit),
                        'swap': float(swap),           # 🔧 FIXED: ใช้ตัวแปรที่ได้จาก getattr
                        'commission': float(commission), # 🔧 FIXED: ใช้ตัวแปรที่ได้จาก getattr
                        'magic': magic,                # 🔧 FIXED
                        'comment': comment,            # 🔧 FIXED
                        'time_open': datetime.fromtimestamp(pos.time),
                    }
                    
                    # คำนวณข้อมูลเพิ่มเติม
                    open_time = position_data['time_open']
                    age_timedelta = current_time - open_time
                    
                    position_data['age'] = self._format_position_age(age_timedelta)
                    position_data['age_hours'] = age_timedelta.total_seconds() / 3600
                    position_data['age_minutes'] = age_timedelta.total_seconds() / 60
                    
                    # 🔧 FIXED: คำนวณ total P&L อย่างปลอดภัย
                    total_pnl = position_data['profit'] + position_data['swap'] + position_data['commission']
                    position_data['total_pnl'] = round(total_pnl, 2)
                    
                    # คำนวณ pips/points movement
                    position_data['pips_movement'] = self._calculate_pips_movement(position_data)
                    
                    # จำแนกประเภท position
                    position_data['status'] = self._classify_position_status(position_data)
                    
                    processed_positions.append(position_data)
                    
                    print(f"💰 Position {pos.ticket}: ${total_pnl:.2f} P&L ({position_data['status']})")
                    
                except Exception as e:
                    # 🔧 FIXED: แสดง error ที่ละเอียดขึ้น
                    ticket = getattr(pos, 'ticket', 'unknown')
                    print(f"❌ Error processing position {ticket}: {e}")
                    continue
            
            # อัพเดท cache
            self.position_cache = {pos['id']: pos for pos in processed_positions}
            self.last_update_time = current_time
            
            print(f"📊 Retrieved {len(processed_positions)} valid positions")
            return processed_positions
            
        except Exception as e:
            print(f"❌ Get positions error: {e}")
            return []
            
    def _classify_position_status(self, position: Dict) -> str:
        """🏷️ จำแนกสถานะของ Position"""
        try:
            profit = position.get('total_pnl', 0)
            age_hours = position.get('age_hours', 0)
            
            if profit > self.min_profit_to_close:
                return 'profitable'
            elif profit < self.max_single_loss:
                return 'heavy_loss'
            elif age_hours > self.max_losing_age_hours and profit < 0:
                return 'old_losing'
            elif profit < 0:
                return 'losing'
            else:
                return 'neutral'
                
        except Exception as e:
            print(f"❌ Position classification error: {e}")
            return 'unknown'
    
    def _format_position_age(self, age_timedelta: timedelta) -> str:
        """⏱️ จัดรูปแบบอายุ Position"""
        try:
            total_seconds = int(age_timedelta.total_seconds())
            
            if total_seconds < 60:
                return f"{total_seconds}s"
            elif total_seconds < 3600:
                minutes = total_seconds // 60
                return f"{minutes}m"
            elif total_seconds < 86400:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                return f"{hours}h{minutes}m"
            else:
                days = total_seconds // 86400
                hours = (total_seconds % 86400) // 3600
                return f"{days}d{hours}h"
                
        except Exception as e:
            print(f"❌ Age formatting error: {e}")
            return "unknown"
    
    def _calculate_pips_movement(self, position: Dict) -> float:
        """📏 คำนวณการเคลื่อนไหวเป็น pips"""
        try:
            open_price = position.get('price_open', 0)
            current_price = position.get('price_current', 0)
            position_type = position.get('type', 'BUY')
            
            if open_price <= 0 or current_price <= 0:
                return 0.0
            
            # คำนวณ pips movement
            if position_type == 'BUY':
                pips = (current_price - open_price) * 10000  # สำหรับทองคำ
            else:  # SELL
                pips = (open_price - current_price) * 10000
            
            return round(pips, 1)
            
        except Exception as e:
            print(f"❌ Pips calculation error: {e}")
            return 0.0
    
    # ==========================================
    # 🧠 SMART CLOSE ANALYSIS
    # ==========================================
    
    def check_smart_close_opportunities(self) -> List[Dict]:
        """
        🧠 หาโอกาสปิดออเดอร์อัจฉริยะ (ไม่มี Emergency/Aging)
        
        Returns:
            List[Dict]: รายการ close actions ที่แนะนำ
        """
        try:
            positions = self.get_all_positions()
            
            if not positions:
                return []
            
            close_opportunities = []
            
            # 1. Smart Recovery Analysis
            recovery_actions = self._find_recovery_opportunities(positions)
            close_opportunities.extend(recovery_actions)
            
            # 2. Portfolio Balance Analysis  
            balance_actions = self._find_balance_opportunities(positions)
            close_opportunities.extend(balance_actions)
            
            # 3. Profit Target Analysis
            profit_actions = self._find_profit_opportunities(positions)
            close_opportunities.extend(profit_actions)
            
            
            # เรียงตาม priority
            close_opportunities.sort(key=lambda x: x.get('priority', 5))
            
            if close_opportunities:
                print(f"🧠 Found {len(close_opportunities)} smart close opportunities")
            
            return close_opportunities
            
        except Exception as e:
            print(f"❌ Smart close analysis error: {e}")
        return []
        
    def _find_recovery_opportunities(self, positions: List[Dict]) -> List[Dict]:
        """🎯 หาโอกาส Smart Recovery"""
        try:
            recovery_actions = []
            
            # แยก profitable และ losing positions
            profitable_positions = [p for p in positions if p.get('total_pnl', 0) > self.min_profit_to_close]
            losing_positions = [p for p in positions if p.get('status') in ['losing', 'old_losing', 'heavy_loss']]
            
            if not profitable_positions or not losing_positions:
                return recovery_actions
            
            print(f"🎯 Recovery analysis: {len(profitable_positions)} profitable vs {len(losing_positions)} losing")
            
            # หาการจับคู่ที่เหมาะสม
            for losing_pos in losing_positions:
                losing_amount = abs(losing_pos.get('total_pnl', 0))
                
                # หา profitable positions ที่พอชดเชย
                recovery_candidates = []
                total_recovery_profit = 0
                
                for profit_pos in profitable_positions:
                    profit_amount = profit_pos.get('total_pnl', 0)
                    
                    if profit_amount >= self.min_profit_to_close:
                        recovery_candidates.append(profit_pos)
                        total_recovery_profit += profit_amount
                        
                        # ถ้าพอชดเชยแล้วหยุด
                        if total_recovery_profit >= losing_amount * 1.1:  # พอชดเชย + กำไรเล็กน้อย
                            break
                
                # ถ้าหาได้และคุ้มค่า
                if recovery_candidates and total_recovery_profit >= losing_amount * 0.8:
                    recovery_action = {
                        'action_type': 'smart_recovery',
                        'losing_position': losing_pos['id'],
                        'recovery_positions': [p['id'] for p in recovery_candidates],
                        'losing_amount': losing_amount,
                        'recovery_amount': total_recovery_profit,
                        'net_result': total_recovery_profit - losing_amount,
                        'priority': 2,  # สำคัญปานกลาง
                        'reason': f"Recovery: ${total_recovery_profit:.2f} covers ${losing_amount:.2f} loss"
                    }
                    
                    recovery_actions.append(recovery_action)
            
            return recovery_actions
            
        except Exception as e:
            print(f"❌ Recovery opportunities error: {e}")
            return []
    
    def _find_balance_opportunities(self, positions: List[Dict]) -> List[Dict]:
        """⚖️ หาโอกาสปรับสมดุล Portfolio"""
        try:
            balance_actions = []
            
            # นับ BUY vs SELL positions
            buy_positions = [p for p in positions if p.get('type') == 'BUY']
            sell_positions = [p for p in positions if p.get('type') == 'SELL']
            
            buy_count = len(buy_positions)
            sell_count = len(sell_positions)
            total_count = buy_count + sell_count
            
            if total_count < 4:  # ไม่พอสำหรับ balance analysis
                return balance_actions
            
            # คำนวณอัตราส่วน
            buy_ratio = buy_count / total_count
            sell_ratio = sell_count / total_count
            
            print(f"⚖️ Portfolio balance: {buy_count} BUY ({buy_ratio:.1%}) vs {sell_count} SELL ({sell_ratio:.1%})")
            
            # ตรวจหาความไม่สมดุลมากเกินไป
            if buy_ratio > self.portfolio_balance_threshold:
                # BUY เยอะเกินไป - หาโอกาสปิด BUY
                close_candidates = sorted(
                    buy_positions, 
                    key=lambda x: (x.get('total_pnl', 0), -x.get('age_hours', 0))
                )
                
                # เลือกปิดบางส่วน
                close_count = max(1, int((buy_count - sell_count) / 2))
                positions_to_close = close_candidates[:close_count]
                
                if positions_to_close:
                    balance_action = {
                        'action_type': 'portfolio_balance',
                        'positions_to_close': [p['id'] for p in positions_to_close],
                        'balance_issue': 'too_many_buy',
                        'current_ratio': f"{buy_ratio:.1%} BUY",
                        'priority': 3,
                        'reason': f"Rebalance: Too many BUY positions ({buy_ratio:.1%})"
                    }
                    balance_actions.append(balance_action)
            
            elif sell_ratio > self.portfolio_balance_threshold:
                # SELL เยอะเกินไป - หาโอกาสปิด SELL  
                close_candidates = sorted(
                    sell_positions,
                    key=lambda x: (x.get('total_pnl', 0), -x.get('age_hours', 0))
                )
                
                close_count = max(1, int((sell_count - buy_count) / 2))
                positions_to_close = close_candidates[:close_count]
                
                if positions_to_close:
                    balance_action = {
                        'action_type': 'portfolio_balance', 
                        'positions_to_close': [p['id'] for p in positions_to_close],
                        'balance_issue': 'too_many_sell',
                        'current_ratio': f"{sell_ratio:.1%} SELL",
                        'priority': 3,
                        'reason': f"Rebalance: Too many SELL positions ({sell_ratio:.1%})"
                    }
                    balance_actions.append(balance_action)
            
            return balance_actions
            
        except Exception as e:
            print(f"❌ Balance opportunities error: {e}")
            return []
    
    def _find_profit_opportunities(self, positions: List[Dict]) -> List[Dict]:
        """💰 หาโอกาสปิดเพื่อกำไร (ปรับเงื่อนไข)"""
        try:
            profit_actions = []
            
            # หา positions ที่กำไรดี
            profitable_positions = [
                p for p in positions 
                if p.get('total_pnl', 0) >= self.min_profit_to_close
            ]
            
            if not profitable_positions:
                return profit_actions
            
            # เรียงตามกำไรจากมากไปน้อย
            profitable_positions.sort(key=lambda x: x.get('total_pnl', 0), reverse=True)
            
            # วิเคราะห์แต่ละ position - ปรับเงื่อนไขให้เข้มงวดขึ้น
            for pos in profitable_positions:
                profit = pos.get('total_pnl', 0)
                age_hours = pos.get('age_hours', 0)
                
                # เกณฑ์การปิดเพื่อกำไร - เข้มงวดขึ้น
                close_profit = False
                priority = 4  # ปกติ
                reason = ""
                
                if profit >= 100.0:  # กำไรมากมาก (เพิ่มจาก 50)
                    close_profit = True
                    priority = 1  # สำคัญมาก
                    reason = f"Very high profit: ${profit:.2f}"
                    
                elif profit >= 50.0 and age_hours >= 4:  # กำไรมาก + อายุพอสมควร (เพิ่มจาก 2h)
                    close_profit = True
                    priority = 2
                    reason = f"High profit with age: ${profit:.2f} ({age_hours:.1f}h)"
                    
                elif profit >= 20.0 and age_hours >= 24:  # กำไรปานกลาง + อายุมาก (เพิ่มจาก 12h)
                    close_profit = True
                    priority = 3
                    reason = f"Medium profit but very old: ${profit:.2f} ({age_hours:.1f}h)"
                
                # 🔧 เข้มงวดขึ้น - ไม่ปิดกำไรเล็กๆ แม้จะเก่า
                
                if close_profit:
                    profit_action = {
                        'action_type': 'profit_target',
                        'position_id': pos['id'],
                        'profit_amount': profit,
                        'age_hours': age_hours,
                        'priority': priority,
                        'reason': reason
                    }
                    profit_actions.append(profit_action)
            
            return profit_actions
            
        except Exception as e:
            print(f"❌ Profit opportunities error: {e}")
            return []        
    
    # ==========================================
    # ⚡ CLOSE EXECUTION METHODS
    # ==========================================
    
    def execute_close_action(self, close_action: Dict) -> bool:
        """
        ⚡ ดำเนินการปิดออเดอร์ตาม Action (ไม่มี Emergency/Aging)
        
        Args:
            close_action: ข้อมูล close action
            
        Returns:
            bool: สำเร็จหรือไม่
        """
        try:
            action_type = close_action.get('action_type')
            priority = close_action.get('priority', 5)
            reason = close_action.get('reason', '')
            
            print(f"⚡ Executing close action: {action_type}")
            print(f"   Priority: {priority}")  
            print(f"   Reason: {reason}")
            
            success = False
            
            if action_type == 'smart_recovery':
                success = self._execute_recovery_close(close_action)
                
            elif action_type == 'portfolio_balance':
                success = self._execute_balance_close(close_action)
                
            elif action_type == 'profit_target':
                success = self._execute_profit_close(close_action)
                            
            else:
                print(f"❌ Unknown action type: {action_type}")
                return False
            
            # บันทึกสถิติ
            if success:
                self._record_close_stats(action_type)
                self.position_cache = {}  # Clear cache เพื่อให้อัพเดท
            
            return success
            
        except Exception as e:
            print(f"❌ Close action execution error: {e}")
            return False
    
    def _execute_recovery_close(self, action: Dict) -> bool:
        """🎯 ดำเนินการ Smart Recovery"""
        try:
            losing_id = action.get('losing_position')
            recovery_ids = action.get('recovery_positions', [])
            
            all_positions_to_close = [losing_id] + recovery_ids
            
            print(f"🎯 Smart Recovery: Closing {len(all_positions_to_close)} positions")
            print(f"   Losing: {losing_id}")
            print(f"   Recovery: {recovery_ids}")
            
            return self._close_multiple_positions(all_positions_to_close, "Smart Recovery")
            
        except Exception as e:
            print(f"❌ Recovery close error: {e}")
            return False
    
    def _execute_balance_close(self, action: Dict) -> bool:
        """⚖️ ดำเนินการ Portfolio Balance"""
        try:
            positions_to_close = action.get('positions_to_close', [])
            balance_issue = action.get('balance_issue', '')
            
            print(f"⚖️ Portfolio Balance: Closing {len(positions_to_close)} positions")
            print(f"   Issue: {balance_issue}")
            
            return self._close_multiple_positions(positions_to_close, "Portfolio Balance")
            
        except Exception as e:
            print(f"❌ Balance close error: {e}")
            return False
    
    def _execute_profit_close(self, action: Dict) -> bool:
        """💰 ดำเนินการปิดเพื่อกำไร"""
        try:
            position_id = action.get('position_id')
            profit_amount = action.get('profit_amount', 0)
            
            print(f"💰 Profit Close: Position {position_id} (${profit_amount:.2f})")
            
            return self.close_position_by_id(position_id, "Profit Target")
            
        except Exception as e:
            print(f"❌ Profit close error: {e}")
            return False
            
    # ==========================================
    # 🔧 CORE CLOSE METHODS
    # ==========================================
    
    def close_position_by_id(self, position_id: int, reason: str = "Manual") -> bool:
        """
        ❌ ปิด Position ตาม ID
        
        Args:
            position_id: ID ของ position
            reason: เหตุผลการปิด
            
        Returns:
            bool: สำเร็จหรือไม่
        """
        try:
            if not self.mt5_connector.is_connected:
                print(f"❌ MT5 not connected - cannot close position")
                return False
            
            # ดึงข้อมูล position
            position = mt5.positions_get(ticket=position_id)
            
            if not position:
                print(f"❌ Position {position_id} not found")
                return False
            
            pos = position[0]  # เอาตัวแรก
            
            print(f"❌ Closing position {position_id}...")
            print(f"   Type: {'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL'}")
            print(f"   Volume: {pos.volume} lots")
            print(f"   Profit: ${pos.profit:.2f}")
            print(f"   Reason: {reason}")
            
            # เตรียม close request
            if pos.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(pos.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(pos.symbol).ask
            
            close_request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': pos.symbol,
                'volume': pos.volume,
                'type': order_type,
                'position': position_id,
                'price': price,
                'deviation': 10,
                'magic': pos.magic,
                'comment': f"Close_{reason}",
                'type_time': mt5.ORDER_TIME_GTC,
                'type_filling': mt5.ORDER_FILLING_IOC
            }
            
            # ส่งคำสั่งปิด
            result = mt5.order_send(close_request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Position {position_id} closed successfully")
                print(f"   Close price: ${result.price:.2f}")
                print(f"   Final profit: ${result.profit:.2f}" if hasattr(result, 'profit') else "")
                return True
            else:
                error_msg = f"retcode: {result.retcode}, comment: {result.comment}" if result else "No result"
                print(f"❌ Failed to close position {position_id}: {error_msg}")
                return False
            
        except Exception as e:
            print(f"❌ Close position error: {e}")
            return False
    
    def _close_multiple_positions(self, position_ids: List[int], reason: str = "Batch") -> bool:
        """
        📦 ปิดหลาย Positions พร้อมกัน
        
        Args:
            position_ids: รายการ position IDs
            reason: เหตุผลการปิด
            
        Returns:
            bool: สำเร็จทั้งหมดหรือไม่
        """
        try:
            if not position_ids:
                print(f"ℹ️ No positions to close")
                return True
            
            print(f"📦 Batch closing {len(position_ids)} positions...")
            print(f"   Reason: {reason}")
            print(f"   Position IDs: {position_ids}")
            
            success_count = 0
            total_count = len(position_ids)
            
            for position_id in position_ids:
                if self.close_position_by_id(position_id, reason):
                    success_count += 1
                    time.sleep(0.1)  # พัก 100ms ระหว่างการปิด
            
            success_rate = success_count / total_count
            
            print(f"📦 Batch close result: {success_count}/{total_count} successful ({success_rate:.1%})")
            
            return success_rate >= 0.8  # ถือว่าสำเร็จถ้าปิดได้อย่างน้อย 80%
            
        except Exception as e:
            print(f"❌ Batch close error: {e}")
            return False
    
    def emergency_close_all(self) -> int:
        """
        🚨 ปิดออเดอร์ทั้งหมดฉุกเฉิน
        
        Returns:
            int: จำนวนออเดอร์ที่ปิดได้
        """
        try:
            print(f"🚨 EMERGENCY CLOSE ALL POSITIONS!")
            
            positions = self.get_all_positions()
            
            if not positions:
                print(f"ℹ️ No positions to close")
                return 0
            
            position_ids = [p['id'] for p in positions]
            
            print(f"🚨 Force closing {len(positions)} positions...")
            
            closed_count = 0
            for position_id in position_ids:
                if self.close_position_by_id(position_id, "EMERGENCY STOP"):
                    closed_count += 1
                time.sleep(0.05)  # พักสั้นๆ เพื่อไม่ให้ server งง
            
            print(f"🚨 Emergency close completed: {closed_count}/{len(positions)} closed")
            
            # บันทึกสถิติ
            self.close_stats['emergency_closes'] += closed_count
            
            return closed_count
            
        except Exception as e:
            print(f"❌ Emergency close all error: {e}")
            return 0
    
    # ==========================================
    # 📊 STATISTICS & UTILITY METHODS
    # ==========================================
    
    def _record_close_stats(self, action_type: str):
        """📝 บันทึกสถิติการปิดออเดอร์ (ไม่นับ Emergency)"""
        try:
            if action_type == 'smart_recovery':
                self.close_stats['recovery_closes'] += 1
            elif action_type == 'profit_target':
                self.close_stats['profit_closes'] += 1
            self.close_stats['smart_closes'] += 1
            
        except Exception as e:
            print(f"❌ Close stats recording error: {e}")
    
    def get_portfolio_summary(self) -> Dict:
        """📊 สรุปสถานะ Portfolio"""
        try:
            positions = self.get_all_positions()
            
            if not positions:
                return {
                    'total_positions': 0,
                    'total_pnl': 0.0,
                    'buy_positions': 0,
                    'sell_positions': 0,
                    'profitable_positions': 0,
                    'losing_positions': 0
                }
            
            # นับและรวม
            buy_count = len([p for p in positions if p.get('type') == 'BUY'])
            sell_count = len([p for p in positions if p.get('type') == 'SELL'])
            profitable_count = len([p for p in positions if p.get('total_pnl', 0) > 0])
            losing_count = len([p for p in positions if p.get('total_pnl', 0) < 0])
            
            total_pnl = sum(p.get('total_pnl', 0) for p in positions)
            total_volume = sum(p.get('volume', 0) for p in positions)
            
            # อายุเฉลี่ย
            ages = [p.get('age_hours', 0) for p in positions]
            avg_age_hours = statistics.mean(ages) if ages else 0
            
            return {
                'total_positions': len(positions),
                'total_pnl': total_pnl,
                'total_volume': total_volume,
                'buy_positions': buy_count,
                'sell_positions': sell_count,
                'profitable_positions': profitable_count,
                'losing_positions': losing_count,
                'avg_age_hours': avg_age_hours,
                'buy_sell_ratio': buy_count / max(sell_count, 1),
                'profit_loss_ratio': profitable_count / max(losing_count, 1)
            }
            
        except Exception as e:
            print(f"❌ Portfolio summary error: {e}")
            return {'error': str(e)}
    
    def get_close_statistics(self) -> Dict:
        """📊 สถิติการปิดออเดอร์"""
        return self.close_stats.copy()
    
    def _is_cache_valid(self) -> bool:
        """🔧 ตรวจสอบ Cache"""
        time_diff = (datetime.now() - self.last_update_time).total_seconds()
        return time_diff < self.cache_duration_seconds and bool(self.position_cache)
    
    def is_ready(self) -> bool:
        """✅ ตรวจสอบความพร้อม"""
        return (
            self.mt5_connector is not None and
            self.mt5_connector.is_connected
        )
    
    def get_monitor_info(self) -> Dict:
        """ℹ️ ข้อมูล Position Monitor"""
        return {
            'name': 'Smart Position Monitor',
            'version': '1.0.0',
            'symbol': self.symbol,
            'max_losing_age_hours': self.max_losing_age_hours,
            'min_profit_to_close': self.min_profit_to_close,
            'max_total_loss': self.max_total_loss,
            'max_single_loss': self.max_single_loss,
            'portfolio_balance_threshold': self.portfolio_balance_threshold,
            'cache_duration_seconds': self.cache_duration_seconds
        }