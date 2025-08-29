"""
🧠 Smart Order Role Manager - ระบบจัดการหน้าที่ออเดอร์อัจฉริยะ (FIXED)
order_role_manager.py

🎯 CORE CONCEPT:
✅ จำแนกหน้าที่ออเดอร์อัตโนมัติ (MAIN/HG/SUPPORT/SACRIFICE)
✅ ปรับหน้าที่ตาม market condition แบบ dynamic
✅ ปิดออเดอร์แบบ intelligent pairing (กำไร + ขาดทุน = net positive)
✅ ระบบ sacrifice ออเดอร์เสียเพื่อช่วยพอร์ต (เมื่อจำเป็น)
✅ Flexible decision making - ไม่ติดกฎตายตัว

🔧 FIXED: ใช้ position_monitor.close_position_by_id() แทน _close_position_by_id()
"""

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import statistics
import time

class SmartOrderRoleManager:
    """
    🧠 Smart Order Role Manager - FIXED VERSION
    
    จัดการหน้าที่ของออเดอร์และตัดสินใจปิดออเดอร์อย่างฉลาด
    ✅ ใช้ position_monitor สำหรับการปิดออเดอร์
    """
    
    def __init__(self, mt5_connector, config: Dict):
        """
        🔧 เริ่มต้น Smart Order Role Manager - FIXED
        """
        self.mt5_connector = mt5_connector
        self.config = config
        
        # ✅ เพิ่ม position_monitor reference
        self.position_monitor = None  # จะถูกตั้งค่าจาก main.py
        
        # การตั้งค่า role management
        self.role_config = config.get("role_management", {})
        self.symbol = config.get("trading", {}).get("symbol", "XAUUSD.v")
        
        # 🎯 ROLE DEFINITIONS
        self.roles = {
            'MAIN': 'ออเดอร์หลักที่ follow trend',
            'HG': 'ออเดอร์ป้องกัน (Hedge Guard)',
            'SUPPORT': 'ออเดอร์สำรองรอโอกาส',
            'SACRIFICE': 'ออเดอร์ที่พร้อมสละเพื่อพอร์ต'
        }
        
        # 🧠 SMART SETTINGS
        self.min_net_profit_to_close = self.role_config.get("min_net_profit_to_close", 5.0)  # $5 net กำไรขั้นต่ำ
        self.max_sacrifice_loss = self.role_config.get("max_sacrifice_loss", 30.0)  # ยอมเสีย $30 เพื่อได้กำไร
        self.hedge_ratio_threshold = self.role_config.get("hedge_ratio_threshold", 0.4)  # 40% ของออเดอร์เป็น hedge
        self.min_main_positions = self.role_config.get("min_main_positions", 2)  # MAIN อย่างน้อย 2 ออเดอร์
        
        # Profit/Loss thresholds
        self.profit_target_base = self.role_config.get("profit_target_base", 30.0)  # $30/lot
        self.acceptable_loss_threshold = self.role_config.get("acceptable_loss_threshold", -50.0)  # -$50 ต่อออเดอร์
        
        # Timing settings
        self.min_position_age_minutes = self.role_config.get("min_position_age_minutes", 30)  # อายุขั้นต่ำ 30 นาที
        self.max_sacrifice_age_hours = self.role_config.get("max_sacrifice_age_hours", 12)  # SACRIFICE ต้องไม่เก่าเกิน 12 ชม
        
        # 📊 TRACKING VARIABLES
        self.order_roles = {}  # {position_id: role}
        self.role_history = []  # ประวัติการเปลี่ยน role
        self.last_role_assignment_time = datetime.min
        self.execution_history = []  # ประวัติการปิดออเดอร์
        
        # Performance tracking
        self.role_performance = {
            'MAIN': {'closed_count': 0, 'total_profit': 0.0},
            'HG': {'closed_count': 0, 'total_profit': 0.0},
            'SACRIFICE': {'closed_count': 0, 'total_profit': 0.0},
            'SUPPORT': {'closed_count': 0, 'total_profit': 0.0}
        }
        
        print(f"🧠 Smart Order Role Manager initialized")
        print(f"   Min net profit: ${self.min_net_profit_to_close}")
        print(f"   Max sacrifice loss: ${self.max_sacrifice_loss}")
    
    def set_position_monitor(self, position_monitor):
        """🔗 ตั้งค่า position monitor reference - NEW METHOD"""
        self.position_monitor = position_monitor
        print(f"🔗 Position monitor linked to Role Manager")
    
    def _get_position_attribute(self, pos: Any, attr_name: str, default: Any = None) -> Any:
        """🔧 ดึง attribute จาก position ไม่ว่าจะเป็น dict หรือ object"""
        try:
            if isinstance(pos, dict):
                return pos.get(attr_name, default)
            else:
                return getattr(pos, attr_name, default)
        except Exception as e:
            return default

    def analyze_and_assign_roles(self, positions: List[Dict]) -> Dict:
        """
        🧠 วิเคราะห์และจัดหน้าที่ออเดอร์อัจฉริยะ
        
        Returns:
            Dict: ผลการจัดหน้าที่ + คำแนะนำ
        """
        try:
            if not positions:
                return {'assignments': {}, 'recommendations': []}
            
            current_price = self._get_current_price()
            if not current_price:
                return {'assignments': {}, 'recommendations': [], 'error': 'Cannot get current price'}
            
            print(f"🧠 Smart Role Analysis - Current Price: ${current_price:.2f}")
            print(f"📊 Analyzing {len(positions)} positions...")
            
            # แยก BUY/SELL positions
            buy_positions = [p for p in positions if p.get('type') == 'buy']
            sell_positions = [p for p in positions if p.get('type') == 'sell']
            
            # จัดเรียงตามระยะห่างจากราคาปัจจุบัน
            buy_positions.sort(key=lambda x: abs(current_price - x.get('price_open', 0)))
            sell_positions.sort(key=lambda x: abs(current_price - x.get('price_open', 0)))
            
            # 🎯 ASSIGN ROLES
            role_assignments = {}
            
            # 1. MAIN ROLES - ออเดอร์ที่ใกล้กำไรที่สุด
            if buy_positions:
                closest_profitable_buy = self._find_closest_profitable_position(buy_positions, current_price, 'buy')
                if closest_profitable_buy:
                    role_assignments[closest_profitable_buy['id']] = 'MAIN'
            
            if sell_positions:
                closest_profitable_sell = self._find_closest_profitable_position(sell_positions, current_price, 'sell')
                if closest_profitable_sell:
                    role_assignments[closest_profitable_sell['id']] = 'MAIN'
            
            # 2. HEDGE GUARD ROLES - ออเดอร์ป้องกัน
            self._assign_hedge_roles(buy_positions, sell_positions, current_price, role_assignments)
            
            # 3. SACRIFICE ROLES - ออเดอร์ที่แย่ที่สุด
            self._assign_sacrifice_roles(positions, current_price, role_assignments)
            
            # 4. SUPPORT ROLES - ออเดอร์ที่เหลือ
            for pos in positions:
                if pos['id'] not in role_assignments:
                    role_assignments[pos['id']] = 'SUPPORT'
            
            # อัพเดท internal tracking
            self.order_roles = role_assignments.copy()
            self.last_role_assignment_time = datetime.now()
            
            # 🎯 GENERATE SMART RECOMMENDATIONS
            recommendations = self._generate_smart_recommendations(positions, role_assignments, current_price)
            
            print(f"✅ Role Assignment Complete:")
            for role in ['MAIN', 'HG', 'SUPPORT', 'SACRIFICE']:
                count = sum(1 for r in role_assignments.values() if r == role)
                if count > 0:
                    print(f"   {role}: {count} positions")
            
            return {
                'assignments': role_assignments,
                'recommendations': recommendations,
                'analysis_time': datetime.now(),
                'market_context': self._get_market_context(current_price, positions)
            }
            
        except Exception as e:
            print(f"❌ Role analysis error: {e}")
            return {'assignments': {}, 'recommendations': [], 'error': str(e)}
    
    def _find_closest_profitable_position(self, positions: List[Dict], current_price: float, position_type: str) -> Optional[Dict]:
        """หา position ที่ใกล้กำไรที่สุด"""
        try:
            profitable_positions = []
            
            for pos in positions:
                entry_price = pos.get('price_open', 0)
                current_pnl = pos.get('total_pnl', 0)
                
                # คำนวณระยะห่างจากกำไร
                if position_type == 'buy':
                    distance_to_profit = max(0, entry_price - current_price)  # ต้องการราคาขึ้น
                else:  # sell
                    distance_to_profit = max(0, current_price - entry_price)  # ต้องการราคาลง
                
                # เลือก positions ที่มีโอกาสกำไร
                if current_pnl > -20 and distance_to_profit < 2.0:  # ขาดทุนไม่เกิน $20 และใกล้กำไร < $2
                    profitable_positions.append(pos)
            
            # เรียงตามความใกล้กำไร
            if profitable_positions:
                return min(profitable_positions, key=lambda x: abs(x.get('total_pnl', 0)))
            
            return None
            
        except Exception as e:
            print(f"❌ Find profitable position error: {e}")
            return None
    
    def _assign_hedge_roles(self, buy_positions: List[Dict], sell_positions: List[Dict], 
                           current_price: float, role_assignments: Dict):
        """จัด HG roles ให้ positions ที่เป็น hedge"""
        try:
            # หา positions ที่ขาดทุนแต่อยู่ในระยะ hedge
            hedge_candidates = []
            
            for pos in buy_positions + sell_positions:
                if pos['id'] in role_assignments:  # ถ้าได้ role แล้ว ข้าม
                    continue
                
                pnl = pos.get('total_pnl', 0)
                
                # เงื่อนไข HG: ขาดทุนพอสมควรแต่ไม่มาก
                if -40 <= pnl <= -10:
                    hedge_candidates.append(pos)
            
            # เลือก HG positions (ไม่เกิน 30% ของ total)
            max_hg_positions = max(1, len(buy_positions + sell_positions) // 3)
            hedge_candidates.sort(key=lambda x: x.get('total_pnl', 0))  # เรียงจากขาดทุนน้อยสุด
            
            for i, pos in enumerate(hedge_candidates[:max_hg_positions]):
                role_assignments[pos['id']] = 'HG'
            
        except Exception as e:
            print(f"❌ Assign hedge roles error: {e}")
    
    def _assign_sacrifice_roles(self, positions: List[Dict], current_price: float, role_assignments: Dict):
        """จัด SACRIFICE roles ให้ positions ที่แย่ที่สุด"""
        try:
            sacrifice_candidates = []
            
            for pos in positions:
                if pos['id'] in role_assignments:  # ถ้าได้ role แล้ว ข้าม
                    continue
                
                pnl = pos.get('total_pnl', 0)
                
                # เงื่อนไข SACRIFICE: ขาดทุนหนัก หรือ เก่ามาก
                age_hours = pos.get('age_hours', 0)
                
                if pnl < -50 or age_hours > 12:  # ขาดทุน > $50 หรือ เก่า > 12 ชม
                    sacrifice_candidates.append(pos)
            
            # เลือก SACRIFICE positions (ไม่เกิน 20% ของ total)
            max_sacrifice_positions = max(1, len(positions) // 5)
            sacrifice_candidates.sort(key=lambda x: x.get('total_pnl', 0))  # เรียงจากขาดทุนมากสุด
            
            for pos in sacrifice_candidates[:max_sacrifice_positions]:
                role_assignments[pos['id']] = 'SACRIFICE'
                
        except Exception as e:
            print(f"❌ Assign sacrifice roles error: {e}")
    
    def _generate_smart_recommendations(self, positions: List[Dict], role_assignments: Dict, current_price: float) -> List[Dict]:
        """🎯 สร้างคำแนะนำอัจฉริยะ"""
        try:
            recommendations = []
            
            # 1. หาโอกาสเก็บกำไร MAIN
            main_positions = [p for p in positions if role_assignments.get(p['id']) == 'MAIN']
            profit_opportunities = self._find_main_profit_opportunities(main_positions, current_price)
            recommendations.extend(profit_opportunities)
            
            # 2. หาโอกาสปิดคู่ hedge
            hg_positions = [p for p in positions if role_assignments.get(p['id']) == 'HG']
            hedge_opportunities = self._find_hedge_pair_opportunities(positions, hg_positions, current_price)
            recommendations.extend(hedge_opportunities)
            
            # 3. หาโอกาส strategic sacrifice
            sacrifice_positions = [p for p in positions if role_assignments.get(p['id']) == 'SACRIFICE']
            sacrifice_opportunities = self._find_sacrifice_opportunities(sacrifice_positions, positions, current_price)
            recommendations.extend(sacrifice_opportunities)
            
            # 4. หาโอกาส rebalance roles
            rebalance_opportunities = self._find_rebalancing_opportunities(positions, role_assignments, current_price)
            recommendations.extend(rebalance_opportunities)
            
            # เรียงตาม priority
            recommendations.sort(key=lambda x: x.get('priority', 10))
            
            return recommendations
            
        except Exception as e:
            print(f"❌ Generate smart recommendations error: {e}")
            return []
    
    def get_smart_close_recommendation(self) -> Dict:
        """🎯 ดึงคำแนะนำปิดออเดอร์อัจฉริยะ"""
        try:
            # ดึง positions ปัจจุบัน
            raw_positions = mt5.positions_get()
            if not raw_positions:
                return {'action_type': 'wait', 'reason': 'No positions to analyze'}
            
            # แปลงเป็น dict format
            positions = []
            current_time = datetime.now()
            
            for pos in raw_positions:
                open_time = datetime.fromtimestamp(pos.time)
                age = current_time - open_time
                
                position_data = {
                    'id': pos.ticket,
                    'type': 'buy' if pos.type == mt5.POSITION_TYPE_BUY else 'sell',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'total_pnl': pos.profit,
                    'age_hours': age.total_seconds() / 3600,
                    'symbol': pos.symbol
                }
                positions.append(position_data)
            
            # วิเคราะห์และจัด roles
            analysis_result = self.analyze_and_assign_roles(positions)
            recommendations = analysis_result.get('recommendations', [])
            
            if not recommendations:
                return {'action_type': 'wait', 'reason': 'No profitable opportunities found'}
            
            # ส่งคำแนะนำที่ดีที่สุด (priority สูงสุด)
            best_recommendation = recommendations[0]
            
            return best_recommendation
            
        except Exception as e:
            print(f"❌ Smart close recommendation error: {e}")
            return {'action_type': 'wait', 'reason': f'Analysis error: {e}'}
    
    # ==========================================
    # 🎯 EXECUTION ENGINE - FIXED METHODS
    # ==========================================
    
    def execute_smart_recommendation(self, recommendation: Dict) -> Dict:
        """
        ⚡ ดำเนินการตามคำแนะนำอัจฉริยะ - FIXED
        """
        try:
            action_type = recommendation.get('action_type')
            priority = recommendation.get('priority', 10)
            
            print(f"⚡ Executing smart recommendation: {action_type} (Priority: {priority})")
            
            success = False
            execution_details = {}
            
            if action_type == 'main_profit_harvest':
                success, execution_details = self._execute_main_profit_harvest(recommendation)
                
            elif action_type == 'hedge_pair_close':
                success, execution_details = self._execute_hedge_pair_close(recommendation)
                
            elif action_type == 'strategic_sacrifice':
                success, execution_details = self._execute_strategic_sacrifice(recommendation)
                
            elif action_type == 'emergency_portfolio_protection':
                success, execution_details = self._execute_emergency_protection(recommendation)
                
            elif action_type == 'role_rebalance':
                success, execution_details = self._execute_role_rebalance(recommendation)
                
            else:
                return {
                    'success': False,
                    'reason': f'Unknown action type: {action_type}',
                    'recommendation': recommendation
                }
            
            # บันทึกผลลัพธ์
            if success:
                self._record_execution_success(action_type, recommendation, execution_details)
            
            return {
                'success': success,
                'action_type': action_type,
                'execution_details': execution_details,
                'recommendation': recommendation,
                'execution_time': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Smart recommendation execution error: {e}")
            return {
                'success': False,
                'error': str(e),
                'recommendation': recommendation
            }
    
    def _execute_main_profit_harvest(self, recommendation: Dict) -> Tuple[bool, Dict]:
        """💰 ดำเนินการเก็บกำไร MAIN position - FIXED"""
        try:
            position_id = recommendation.get('position_id')
            expected_profit = recommendation.get('profit', 0)
            
            print(f"💰 Harvesting MAIN position {position_id} profit: ${expected_profit:.2f}")
            
            # ✅ ใช้ position_monitor.close_position_by_id() แทน _close_position_by_id()
            if self.position_monitor:
                success = self.position_monitor.close_position_by_id(position_id, "MAIN Profit Harvest")
            else:
                print(f"❌ Position monitor not available")
                return False, {'error': 'Position monitor not available'}
            
            execution_details = {
                'position_id': position_id,
                'expected_profit': expected_profit,
                'close_reason': 'MAIN Profit Harvest'
            }
            
            if success:
                # อัพเดท role performance
                self.role_performance['MAIN']['closed_count'] += 1
                self.role_performance['MAIN']['total_profit'] += expected_profit
                
                # ลบจาก role tracking
                if position_id in self.order_roles:
                    del self.order_roles[position_id]
            
            return success, execution_details
            
        except Exception as e:
            print(f"❌ Main profit harvest error: {e}")
            return False, {'error': str(e)}
    
    def _execute_hedge_pair_close(self, recommendation: Dict) -> Tuple[bool, Dict]:
        """⚖️ ดำเนินการปิดคู่ hedge - FIXED"""
        try:
            hg_id = recommendation.get('hg_position_id')
            partner_id = recommendation.get('partner_position_id')
            expected_net = recommendation.get('net_result', 0)
            
            print(f"⚖️ Closing hedge pair: HG {hg_id} + Partner {partner_id} = ${expected_net:.2f}")
            
            # ✅ ใช้ position_monitor แทน _close_position_by_id()
            if self.position_monitor:
                success1 = self.position_monitor.close_position_by_id(hg_id, "Hedge Pair Close")
                success2 = self.position_monitor.close_position_by_id(partner_id, "Hedge Pair Close")
            else:
                print(f"❌ Position monitor not available")
                return False, {'error': 'Position monitor not available'}
            
            overall_success = success1 and success2
            
            execution_details = {
                'hg_position_id': hg_id,
                'partner_position_id': partner_id,
                'expected_net_result': expected_net,
                'hg_close_success': success1,
                'partner_close_success': success2
            }
            
            if overall_success:
                # อัพเดท performance
                self.role_performance['HG']['closed_count'] += 1
                self.role_performance['HG']['total_profit'] += expected_net
                
                # ลบจาก role tracking
                for pid in [hg_id, partner_id]:
                    if pid in self.order_roles:
                        del self.order_roles[pid]
            
            return overall_success, execution_details
            
        except Exception as e:
            print(f"❌ Hedge pair close error: {e}")
            return False, {'error': str(e)}
    
    def _execute_strategic_sacrifice(self, recommendation: Dict) -> Tuple[bool, Dict]:
        """🎭 ดำเนินการเสีย sacrifice เชิงกลยุทธ์ - FIXED"""
        try:
            sacrifice_id = recommendation.get('sacrifice_position_id')
            profitable_id = recommendation.get('profitable_position_id')
            expected_net = recommendation.get('net_result', 0)
            sacrifice_loss = recommendation.get('sacrifice_loss', 0)
            
            print(f"🎭 Strategic sacrifice: Position {sacrifice_id} (${sacrifice_loss:.2f}) + Profitable {profitable_id} = ${expected_net:.2f}")
            
            # ✅ ใช้ position_monitor แทน _close_position_by_id()
            if self.position_monitor:
                success1 = self.position_monitor.close_position_by_id(sacrifice_id, "Strategic Sacrifice")
                success2 = self.position_monitor.close_position_by_id(profitable_id, "Strategic Sacrifice")
            else:
                print(f"❌ Position monitor not available")
                return False, {'error': 'Position monitor not available'}
            
            overall_success = success1 and success2
            
            execution_details = {
                'sacrifice_position_id': sacrifice_id,
                'profitable_position_id': profitable_id,
                'expected_net_result': expected_net,
                'sacrifice_loss': sacrifice_loss,
                'sacrifice_success': success1,
                'profitable_success': success2
            }
            
            if overall_success:
                # อัพเดท performance
                self.role_performance['SACRIFICE']['closed_count'] += 1
                self.role_performance['SACRIFICE']['total_profit'] += expected_net
                
                # ลบจาก role tracking
                for pid in [sacrifice_id, profitable_id]:
                    if pid in self.order_roles:
                        del self.order_roles[pid]
            
            return overall_success, execution_details
            
        except Exception as e:
            print(f"❌ Strategic sacrifice error: {e}")
            return False, {'error': str(e)}
    
    def _execute_emergency_protection(self, recommendation: Dict) -> Tuple[bool, Dict]:
        """🚨 ดำเนินการป้องกัน emergency - FIXED"""
        try:
            positions_to_close = recommendation.get('positions_to_close', [])
            expected_profit = recommendation.get('emergency_profit', 0)
            
            print(f"🚨 Emergency protection: Closing {len(positions_to_close)} positions for ${expected_profit:.2f}")
            
            close_results = []
            overall_success = True
            
            if not self.position_monitor:
                print(f"❌ Position monitor not available")
                return False, {'error': 'Position monitor not available'}
            
            for position_id in positions_to_close:
                # ✅ ใช้ position_monitor แทน _close_position_by_id()
                success = self.position_monitor.close_position_by_id(position_id, "Emergency Protection")
                close_results.append({'position_id': position_id, 'success': success})
                if not success:
                    overall_success = False
            
            execution_details = {
                'positions_closed': positions_to_close,
                'close_results': close_results,
                'expected_profit': expected_profit,
                'overall_success': overall_success
            }
            
            if overall_success:
                # ลบจาก role tracking
                for pid in positions_to_close:
                    if pid in self.order_roles:
                        del self.order_roles[pid]
            
            return overall_success, execution_details
            
        except Exception as e:
            print(f"❌ Emergency protection error: {e}")
            return False, {'error': str(e)}
    
    def _execute_role_rebalance(self, recommendation: Dict) -> Tuple[bool, Dict]:
        """🔄 ดำเนินการ rebalance role"""
        try:
            position_id = recommendation.get('position_id')
            old_role = recommendation.get('old_role')
            new_role = recommendation.get('new_role')
            
            print(f"🔄 Role rebalance: Position {position_id} from {old_role} to {new_role}")
            
            # อัพเดท role assignment
            if position_id in self.order_roles:
                self.order_roles[position_id] = new_role
            
            # บันทึกประวัติ
            self.role_history.append({
                'timestamp': datetime.now(),
                'position_id': position_id,
                'old_role': old_role,
                'new_role': new_role,
                'reason': recommendation.get('reason', '')
            })
            
            execution_details = {
                'position_id': position_id,
                'old_role': old_role,
                'new_role': new_role,
                'rebalance_time': datetime.now()
            }
            
            return True, execution_details
            
        except Exception as e:
            print(f"❌ Role rebalance error: {e}")
            return False, {'error': str(e)}
    
    # ==========================================
    # 🔧 HELPER METHODS
    # ==========================================
    
    def _get_current_price(self) -> Optional[float]:
        """ดึงราคาปัจจุบัน"""
        try:
            if not self.mt5_connector.is_connected:
                return None
                
            tick = mt5.symbol_info_tick(self.symbol)
            if tick:
                return (tick.bid + tick.ask) / 2
            return None
            
        except Exception as e:
            print(f"❌ Get current price error: {e}")
            return None
    
    def _get_market_context(self, current_price: float, positions: List[Dict]) -> Dict:
        """วิเคราะห์ context ของ market"""
        try:
            return {
                'current_price': current_price,
                'total_positions': len(positions),
                'total_pnl': sum(p.get('total_pnl', 0) for p in positions),
                'buy_positions': len([p for p in positions if p.get('type') == 'buy']),
                'sell_positions': len([p for p in positions if p.get('type') == 'sell']),
                'analysis_time': datetime.now()
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _record_execution_success(self, action_type: str, recommendation: Dict, execution_details: Dict):
        """📝 บันทึกผลการดำเนินการที่สำเร็จ"""
        try:
            self.execution_history.append({
                'timestamp': datetime.now(),
                'action_type': action_type,
                'recommendation': recommendation,
                'execution_details': execution_details,
                'success': True
            })
            
            # จำกัดประวัติไม่เกิน 100 รายการ
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]
                
        except Exception as e:
            print(f"❌ Record execution success error: {e}")
    
    # ==========================================
    # 🎯 OPPORTUNITY FINDING METHODS (เก็บเดิม)
    # ==========================================
    
    def _find_main_profit_opportunities(self, main_positions: List[Dict], current_price: float) -> List[Dict]:
        """💰 หาโอกาสเก็บกำไร MAIN positions"""
        try:
            opportunities = []
            
            for pos in main_positions:
                pnl = pos.get('total_pnl', 0)
                volume = pos.get('volume', 0)
                profit_threshold = self._calculate_dynamic_profit_threshold(pos, current_price)
                
                if pnl >= profit_threshold:
                    opportunities.append({
                        'action_type': 'main_profit_harvest',
                        'position_id': pos['id'],
                        'profit': pnl,
                        'volume': volume,
                        'threshold': profit_threshold,
                        'priority': 2,  # Priority สูง
                        'reason': f'MAIN profit ready: ${pnl:.1f} >= ${profit_threshold:.1f}'
                    })
            
            return opportunities
            
        except Exception as e:
            print(f"❌ Find MAIN profit opportunities error: {e}")
            return []
    
    def _find_hedge_pair_opportunities(self, all_positions: List[Dict], hg_positions: List[Dict], current_price: float) -> List[Dict]:
        """⚖️ หาโอกาสปิดคู่ hedge"""
        try:
            opportunities = []
            
            for hg_pos in hg_positions:
                # หา partner position ที่เหมาะสม
                hg_type = hg_pos.get('type')
                partner_type = 'sell' if hg_type == 'buy' else 'buy'
                
                # หา potential partners
                potential_partners = [
                    p for p in all_positions 
                    if p.get('type') == partner_type and p.get('total_pnl', 0) > 10  # กำไรมากกว่า $10
                ]
                
                for partner in potential_partners:
                    hg_pnl = hg_pos.get('total_pnl', 0)
                    partner_pnl = partner.get('total_pnl', 0)
                    net_result = hg_pnl + partner_pnl
                    
                    if net_result >= self.min_net_profit_to_close:
                        opportunities.append({
                            'action_type': 'hedge_pair_close',
                            'hg_position_id': hg_pos['id'],
                            'partner_position_id': partner['id'],
                            'net_result': net_result,
                            'hg_pnl': hg_pnl,
                            'partner_pnl': partner_pnl,
                            'priority': 3,
                            'reason': f'Hedge pair net profit: ${net_result:.1f}'
                        })
                        break  # หาได้แล้ว หยุด
            
            return opportunities
            
        except Exception as e:
            print(f"❌ Find hedge pair opportunities error: {e}")
            return []
    
    def _find_sacrifice_opportunities(self, sacrifice_positions: List[Dict], all_positions: List[Dict], current_price: float) -> List[Dict]:
        """🎭 หาโอกาส strategic sacrifice"""
        try:
            opportunities = []
            
            # หา profitable positions
            profitable_positions = [
                p for p in all_positions 
                if p.get('total_pnl', 0) > 20  # กำไรมากกว่า $20
            ]
            
            for sacrifice_pos in sacrifice_positions:
                sacrifice_loss = sacrifice_pos.get('total_pnl', 0)
                
                # ต้องเป็นขาดทุน และไม่เกิน max sacrifice loss
                if sacrifice_loss >= 0 or abs(sacrifice_loss) > self.max_sacrifice_loss:
                    continue
                
                # หา profitable position ที่เมื่อรวมแล้วได้กำไร
                for profitable_pos in profitable_positions:
                    profitable_profit = profitable_pos.get('total_pnl', 0)
                    net_result = sacrifice_loss + profitable_profit
                    
                    if net_result >= self.min_net_profit_to_close:
                        opportunities.append({
                            'action_type': 'strategic_sacrifice',
                            'sacrifice_position_id': sacrifice_pos['id'],
                            'profitable_position_id': profitable_pos['id'],
                            'sacrifice_loss': sacrifice_loss,
                            'profitable_profit': profitable_profit,
                            'net_result': net_result,
                            'priority': 5,
                            'reason': f'Strategic sacrifice: Net ${net_result:.1f}'
                        })
                        break  # หาได้แล้ว หยุด
            
            return opportunities
            
        except Exception as e:
            print(f"❌ Find sacrifice opportunities error: {e}")
            return []
    
    def _find_rebalancing_opportunities(self, positions: List[Dict], role_assignments: Dict, current_price: float) -> List[Dict]:
        """🔄 หาโอกาส rebalance roles"""
        try:
            rebalancing_actions = []
            
            # วิเคราะห์ความสมดุลของ roles
            role_counts = {}
            for role in ['MAIN', 'HG', 'SUPPORT', 'SACRIFICE']:
                role_counts[role] = sum(1 for r in role_assignments.values() if r == role)
            
            # ถ้ามี MAIN น้อยเกินไป (ควรมี 2-4 positions)
            if role_counts['MAIN'] < 2:
                # หา SUPPORT positions ที่สามารถเป็น MAIN ได้
                support_positions = [p for p in positions if role_assignments.get(p['id']) == 'SUPPORT']
                suitable_mains = [
                    p for p in support_positions 
                    if p.get('total_pnl', 0) > -30  # ไม่ขาดทุนหนักมาก
                ]
                
                if suitable_mains:
                    best_candidate = min(suitable_mains, key=lambda x: abs(x.get('total_pnl', 0)))
                    
                    rebalancing_actions.append({
                        'action_type': 'role_rebalance',
                        'position_id': best_candidate['id'],
                        'old_role': 'SUPPORT',
                        'new_role': 'MAIN',
                        'priority': 8,
                        'reason': f"Promote SUPPORT to MAIN for better balance"
                    })
            
            return rebalancing_actions
            
        except Exception as e:
            print(f"❌ Rebalancing opportunities error: {e}")
            return []
    
    def _calculate_dynamic_profit_threshold(self, position: Dict, current_price: float) -> float:
        """🎯 คำนวณ profit threshold แบบ dynamic"""
        try:
            volume = self._get_position_attribute(position, 'volume', 0.01)
            age_hours = self._get_position_attribute(position, 'age_hours', 0)
            
            # Base threshold
            base_threshold = self.profit_target_base * volume
            
            # Age factor - ยิ่งเก่า ยิ่งลด threshold
            age_factor = max(0.5, 1 - (age_hours / 24))
            
            # Market volatility factor (ถ้ามี)
            volatility_factor = 1.0  # คงที่ไว้ก่อน
            
            dynamic_threshold = base_threshold * age_factor * volatility_factor
            
            return max(dynamic_threshold, self.min_net_profit_to_close)
            
        except Exception as e:
            return self.min_net_profit_to_close
    
    # ==========================================
    # 📊 STATUS & MONITORING METHODS (เก็บเดิม)
    # ==========================================
    
    def get_role_assignments(self) -> Dict:
        """📋 ดึงการจัดหน้าที่ปัจจุบัน"""
        return self.order_roles.copy()
    
    def get_role_performance(self) -> Dict:
        """📈 ดึงสถิติการทำงานของ roles"""
        return self.role_performance.copy()
    
    def get_execution_history(self, limit: int = 20) -> List[Dict]:
        """📝 ดึงประวัติการดำเนินการ"""
        return self.execution_history[-limit:] if self.execution_history else []
    
    def clear_old_roles(self, active_position_ids: List[int]):
        """🧹 ล้าง roles ของ positions ที่ปิดไปแล้ว"""
        try:
            removed_roles = []
            for position_id in list(self.order_roles.keys()):
                if position_id not in active_position_ids:
                    role = self.order_roles.pop(position_id)
                    removed_roles.append({'position_id': position_id, 'role': role})
            
            if removed_roles:
                print(f"🧹 Cleaned {len(removed_roles)} old role assignments")
            
            return removed_roles
            
        except Exception as e:
            print(f"❌ Clear old roles error: {e}")
            return []
        
    def get_smart_portfolio_health(self, positions: List[Dict]) -> Dict:
        """
        🏥 วิเคราะห์สุขภาพ Portfolio แบบ Smart Role-Aware
        
        Args:
            positions: รายการ positions ทั้งหมด
            
        Returns:
            Dict: ข้อมูลสุขภาพ portfolio อย่างละเอียด
        """
        try:
            if not positions:
                return {
                    'health_score': 1.0,
                    'status': 'empty',
                    'total_positions': 0,
                    'total_pnl': 0.0,
                    'role_distribution': {},
                    'margin_health': {'margin_level': float('inf'), 'status': 'safe'},
                    'recommendations_count': 0,
                    'balance_health': {'buy_ratio': 0.5, 'status': 'balanced'},
                    'risk_factors': []
                }
            
            current_price = self._get_current_price()
            
            # 1. วิเคราะห์และจัด roles
            analysis_result = self.analyze_and_assign_roles(positions)
            role_assignments = analysis_result.get('assignments', {})
            recommendations = analysis_result.get('recommendations', [])
            
            # 2. คำนวณข้อมูลพื้นฐาน
            total_positions = len(positions)
            total_pnl = sum(p.get('total_pnl', 0) for p in positions)
            
            # 3. วิเคราะห์การกระจายของ roles
            role_distribution = {}
            for role in ['MAIN', 'HG', 'SUPPORT', 'SACRIFICE']:
                count = sum(1 for r in role_assignments.values() if r == role)
                role_distribution[role] = {
                    'count': count,
                    'percentage': (count / total_positions * 100) if total_positions > 0 else 0
                }
            
            # 4. วิเคราะห์สมดุล BUY/SELL
            buy_positions = [p for p in positions if p.get('type') == 'buy']
            sell_positions = [p for p in positions if p.get('type') == 'sell']
            buy_volume = sum(p.get('volume', 0) for p in buy_positions)
            sell_volume = sum(p.get('volume', 0) for p in sell_positions)
            total_volume = buy_volume + sell_volume
            
            buy_ratio = buy_volume / total_volume if total_volume > 0 else 0.5
            
            balance_status = 'balanced'
            if buy_ratio > 0.7:
                balance_status = 'buy_heavy'
            elif buy_ratio < 0.3:
                balance_status = 'sell_heavy'
            
            balance_health = {
                'buy_ratio': round(buy_ratio, 3),
                'sell_ratio': round(1 - buy_ratio, 3),
                'buy_volume': round(buy_volume, 2),
                'sell_volume': round(sell_volume, 2),
                'status': balance_status
            }
            
            # 5. วิเคราะห์ Margin Health
            margin_health = {'margin_level': float('inf'), 'status': 'safe'}
            
            if self.mt5_connector and self.mt5_connector.is_connected:
                account_info = self.mt5_connector.get_account_info()
                if account_info:
                    margin = account_info.get('margin', 0)
                    equity = account_info.get('equity', 0)
                    
                    if margin > 0 and equity > 0:
                        margin_level = (equity / margin) * 100
                        margin_health['margin_level'] = round(margin_level, 1)
                        
                        if margin_level <= 150:
                            margin_health['status'] = 'critical'
                        elif margin_level <= 200:
                            margin_health['status'] = 'warning'
                        elif margin_level <= 300:
                            margin_health['status'] = 'good'
                        else:
                            margin_health['status'] = 'excellent'
            
            # 6. คำนวณ Health Score (0-1)
            health_score = self._calculate_portfolio_health_score(
                positions, role_distribution, balance_health, margin_health, recommendations
            )
            
            # 7. กำหนดสถานะรวม
            if health_score >= 0.8:
                overall_status = 'excellent'
            elif health_score >= 0.6:
                overall_status = 'good'
            elif health_score >= 0.4:
                overall_status = 'fair'
            elif health_score >= 0.2:
                overall_status = 'poor'
            else:
                overall_status = 'critical'
            
            # 8. วิเคราะห์ Risk Factors
            risk_factors = self._identify_portfolio_risk_factors(
                positions, role_distribution, balance_health, margin_health
            )
            
            return {
                'health_score': round(health_score, 3),
                'status': overall_status,
                'total_positions': total_positions,
                'total_pnl': round(total_pnl, 2),
                'role_distribution': role_distribution,
                'margin_health': margin_health,
                'balance_health': balance_health,
                'recommendations_count': len(recommendations),
                'top_recommendations': recommendations[:3],  # แสดง 3 อันดับแรก
                'risk_factors': risk_factors,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Portfolio health analysis error: {e}")
            return {
                'health_score': 0.0,
                'status': 'error',
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    def _calculate_portfolio_health_score(self, positions: List[Dict], role_distribution: Dict, 
                                         balance_health: Dict, margin_health: Dict, 
                                         recommendations: List) -> float:
        """🧮 คำนวณคะแนนสุขภาพ Portfolio"""
        try:
            scores = []
            
            # 1. P&L Health Score (30% น้ำหนัก)
            profitable_positions = len([p for p in positions if p.get('total_pnl', 0) > 0])
            pnl_ratio = profitable_positions / len(positions) if positions else 0
            
            pnl_score = 0.5 + (pnl_ratio - 0.5)  # 0.5 = baseline, >0.5 = good
            pnl_score = max(0, min(1, pnl_score))
            scores.append(('pnl', pnl_score, 0.3))
            
            # 2. Balance Health Score (25% น้ำหนัก)
            buy_ratio = balance_health.get('buy_ratio', 0.5)
            imbalance = abs(buy_ratio - 0.5)  # ห่างจาก 50% เท่าไหร่
            balance_score = max(0, 1 - (imbalance / 0.3))  # imbalance > 30% = score 0
            scores.append(('balance', balance_score, 0.25))
            
            # 3. Role Distribution Health (20% น้ำหนัก)
            main_count = role_distribution.get('MAIN', {}).get('count', 0)
            sacrifice_count = role_distribution.get('SACRIFICE', {}).get('count', 0)
            
            role_score = 1.0
            if main_count < 2:  # ต้องมี MAIN อย่างน้อย 2
                role_score -= 0.3
            if sacrifice_count > len(positions) * 0.3:  # SACRIFICE เกิน 30%
                role_score -= 0.4
            
            role_score = max(0, role_score)
            scores.append(('roles', role_score, 0.2))
            
            # 4. Margin Health Score (15% น้ำหนัก)
            margin_level = margin_health.get('margin_level', float('inf'))
            if margin_level == float('inf'):
                margin_score = 1.0
            elif margin_level >= 300:
                margin_score = 1.0
            elif margin_level >= 200:
                margin_score = 0.8
            elif margin_level >= 150:
                margin_score = 0.5
            else:
                margin_score = 0.1
            scores.append(('margin', margin_score, 0.15))
            
            # 5. Opportunity Health Score (10% น้ำหนัก)
            opportunity_score = min(1.0, len(recommendations) / 5)  # มี recommendations = healthy
            scores.append(('opportunities', opportunity_score, 0.1))
            
            # คำนวณคะแนนรวม weighted average
            weighted_sum = sum(score * weight for _, score, weight in scores)
            total_weight = sum(weight for _, _, weight in scores)
            
            final_score = weighted_sum / total_weight if total_weight > 0 else 0
            
            return max(0, min(1, final_score))
            
        except Exception as e:
            print(f"❌ Health score calculation error: {e}")
            return 0.5
    
    def _identify_portfolio_risk_factors(self, positions: List[Dict], role_distribution: Dict, 
                                        balance_health: Dict, margin_health: Dict) -> List[str]:
        """🚨 ระบุปัจจัยเสี่ยง"""
        try:
            risk_factors = []
            
            # 1. P&L Risk Factors
            total_pnl = sum(p.get('total_pnl', 0) for p in positions)
            heavy_loss_positions = len([p for p in positions if p.get('total_pnl', 0) < -100])
            
            if total_pnl < -200:
                risk_factors.append(f"Large total loss: ${total_pnl:.2f}")
            if heavy_loss_positions > 3:
                risk_factors.append(f"Multiple heavy losses: {heavy_loss_positions} positions")
            
            # 2. Balance Risk Factors
            buy_ratio = balance_health.get('buy_ratio', 0.5)
            if buy_ratio > 0.75:
                risk_factors.append(f"Heavy BUY bias: {buy_ratio:.1%}")
            elif buy_ratio < 0.25:
                risk_factors.append(f"Heavy SELL bias: {(1-buy_ratio):.1%}")
            
            # 3. Role Distribution Risks
            main_count = role_distribution.get('MAIN', {}).get('count', 0)
            sacrifice_count = role_distribution.get('SACRIFICE', {}).get('count', 0)
            
            if main_count < 2:
                risk_factors.append(f"Too few MAIN positions: {main_count}")
            if sacrifice_count > len(positions) * 0.3:
                risk_factors.append(f"Too many SACRIFICE positions: {sacrifice_count}")
            
            # 4. Margin Risk Factors
            margin_level = margin_health.get('margin_level', float('inf'))
            if margin_level != float('inf') and margin_level < 200:
                risk_factors.append(f"Low margin level: {margin_level:.1f}%")
            
            # 5. Age Risk Factors
            old_positions = len([p for p in positions if p.get('age_hours', 0) > 24])
            if old_positions > 5:
                risk_factors.append(f"Many old positions: {old_positions} > 24h")
            
            return risk_factors
            
        except Exception as e:
            print(f"❌ Risk factors identification error: {e}")
            return [f"Analysis error: {str(e)}"]